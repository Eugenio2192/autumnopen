from src.tools.config_loader import Configuration
from src.technoeconomical.cost_operations_functions import cost_of_carbon_capture
from src.harmonization.cost_transformation_functions import convert_value, index_generator
import pandas as pd
config = Configuration.get_instance()
pd.set_option('display.max_columns', None)
#idx_map = index_generator()
io = config["IO"]

CLINKER_EMISSION_FACTOR = 0.5  # kgCO2 / kgClinker
CLINKER_CEMENT_RATIO = 0.87  # kgClinker / kgCement

CAPTURE_EFF = config["InputHomogenization"]["CostOfCCConfig"]["DefaultValues"]["CaptureEfficiency"]  # % of CO2 emitted

#COST_OF_CLINKER_REF = convert_value(62.6, idx_map, 2014, 2019, "CEPCI")  # € / t Clinker 2014
#COST_OF_CLINKER_MEA = convert_value(107.4, idx_map, 2014, 2019, "CEPCI")  # -
#COST_OF_CLINKER_OXY = convert_value(93.0, idx_map, 2014, 2019, "CEPCI")  # -

SPECIFIC_POWER_REF = 15.88  # MW / MtCLinker
SPECIFIC_POWER_CAP = 29.5  # MW /MtClinker

CF = 1

ELEC_EMISSION_FACTOR = 0.85  # kg / kWh


def calculate_clinker(annual_production, clinker_cement_ratio):
    """
    Calculate annual clinker production based on given cement/clinker ratio
    :param annual_production: Reported annual production
    :param clinker_cement_ratio: Amount of clinker produced per cement output
    :return: Clinker per year
    """
    return annual_production * clinker_cement_ratio


def calculate_clinker_emissions(clinker_production, emission_factor):
    """
      Calculate emissions per year based on clinker input
      :param clinker_production: Yearly clinker production
      :param clinker_cement_ratio: Amount of clinker produced per cement output
      :return: Clinker per year
      """
    return clinker_production * emission_factor


def calculate_primary_energy_emissions(specific_power, electric_emission_factor):
    """
    Calculate emissions related to primary energy generation
    :param specific_power: Power needed for the production of a Mt of clinker
    :param electric_emission_factor: Emission factor of the energy production
    :return: emissions per year related to energy productoin
    """
    energy = specific_power * CF * 8600  # KWh /  y
    emissions = electric_emission_factor * energy / 1000000  # tCo2 / tclinker
    return emissions


def calculate_total_emisisons(clinker_emissions, power_emissions, capture_ratio=0.0):
    """
    Calculate the added emissions of the cement production unit
    :param clinker_emissions: emissions related to the clinker production
    :param power_emissions: emissions related to the energy production
    :param capture_ratio: Emissions captured through CCS, 0 when no CCS is not used
    :return: Array of emitted and captured amounts
    """
    emissions = (clinker_emissions + power_emissions) * (1 - capture_ratio)
    captured = (clinker_emissions + power_emissions) * capture_ratio
    return emissions, captured


def cost_of_carbon_capture_cement():
    """
    Main function for the calculation of cost of carbon capture from cement production
    :return: dataframe with the cost and amounts
    """
    E_FUEL_REF = calculate_primary_energy_emissions(SPECIFIC_POWER_REF, ELEC_EMISSION_FACTOR)
    E_FUEL_CAP = calculate_primary_energy_emissions(SPECIFIC_POWER_CAP, ELEC_EMISSION_FACTOR)

    df = pd.read_csv(io["CEMENT_INPUT_PATH"], **config["InputConfig"]["iron"])
    data = df["Production"].values
    clinker = (calculate_clinker(val, CLINKER_CEMENT_RATIO) for val in data)
    e_clinker = (calculate_clinker_emissions(val, CLINKER_CEMENT_RATIO) for val in clinker)
    cap_emm_pairs = (calculate_total_emisisons(val, E_FUEL_CAP, CAPTURE_EFF) for val in e_clinker)
    captured = [x[1] for x in cap_emm_pairs]
    cost = [cost_of_carbon_capture(COST_OF_CLINKER_REF, COST_OF_CLINKER_OXY, val) for val in captured]

    df_out = df.copy()
    df_out["AmountCapturedMtY"] = captured
    df_out["CostOfCarbonCaptureEURtonCO2"] = cost
    df_out["Source"] = "Cement"
    df_out["Year"] = 2019

    return df_out


def create():
    """
    Support function for the production of the dataset as a csv file
    """
    df = cost_of_carbon_capture_cement()
    df.to_csv(io["cement_output_path"], index=True)


if __name__ == "__main__":
    create()
