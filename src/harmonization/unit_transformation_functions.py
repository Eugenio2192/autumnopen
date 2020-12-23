import logging
import numpy as np

# Units
BTU_to_KJ = 1.05506
MMBTU_to_GJ = 1.05505585262
lb_to_kg = 0.453592

# Misc Data
# Source : https://phyllis.nl/Biomass/View/1274
illinois_6_HHV = 25.59  # MJ/kg -> GJ/ton
lignite_HHV = 21.33
bit_HHV = 30.2

# Matchers
blacks = ["illinois_6", "Bituminous", "Coal", "China", "black_coal"]
browns = ["victorian_brown", "subbituminous", "Lignite"]
petcoke = ["Petcoke"]


# Factor extraction


def mass_factor(mass_u):
    """
    Helper function to return factors of weight
    :param mass_u: Weight unit as string
    :return: Factor for converting given unit into kg
    """
    if mass_u.lower() == "lb":
        return lb_to_kg
    elif mass_u.lower() == "kg":
        return 1
    elif mass_u.lower() == "ton":
        return 1000
    else:
        msg = "Not a valid Weight Unit"
        logging.warning(msg)
        return np.nan


def elec_factor(elec_u):
    """
    Helper function to transform electricity units to KWh
    :param elec_u: Electricity unit string
    :return: factor for converting given unit into KWh
    """
    if elec_u.lower() == "kwh":
        return 1
    elif elec_u.lower() == "mwh":
        return 1000
    elif elec_u.lower() == "kj":
        return 1 / 3600
    elif elec_u.lower() == "mj":
        return 1 / 3.6
    else:
        msg = "Not a valid Weight Unit"
        logging.warning(msg)
        return np.nan


def heat_factor(heat_u):
    """
    Helper function to transform electricity units to KWh
    :param heat_u: Electricity unit string
    :return: factor for converting given unit into KWh
    """
    if heat_u.upper() == "GJ":
        h_x = 1000000
    elif heat_u.upper() == "MJ":
        h_x = 1000
    elif heat_u.upper() == "BTU":
        h_x = BTU_to_KJ
    elif heat_u.upper() == "KJ":
        h_x = 1
    elif heat_u.upper() == "MMBTU":
        h_x = 1000000 * MMBTU_to_GJ
    else:
        msg = "Not a valid Heat Unit"
        logging.warning(msg)
        return np.nan
    return h_x


# Dimensional match
def hr_dimension_match(hr, units):
    """
    :param hr: Heat Rate in given units
    :param units: Units of the heat rate in the form X_Y where X: Heat units, Y: Electrical Units
    :return: returns Heat Rate in KJ/KWh
    """
    try:
        heat_u, elec_u = [s.upper() for s in units.split("_")]
    except ValueError:
        return hr
    h_x = heat_factor(heat_u)
    e_x = elec_factor(elec_u)
    return hr * h_x / e_x


def plant_emf_dimension_match(plant_emf, units):
    """
    Converts units of the plant emission factor from the Input into Kg per KWh
    :param plant_emf: Value of the emission factor
    :param units: Units in the form X_Y where X is the mass unit and Y is the electricity unit
    :return: Value of emission factor in the form Kg per KWh
    """
    try:
        mass_u, elec_u = [s.upper() for s in units.split("_")]
    except:
        msg = "The Units should be o the form X_Y"
        # logging.warning( msg )
        return plant_emf

    mass_x = mass_factor(mass_u)
    elec_x = elec_factor(elec_u)
    return plant_emf * mass_x / elec_x


def fuel_emf_dimension_match(fuel_emf, units):
    """
    Harmonize fuel emission factors
    :param fuel_emf: Reported emission factor
    :param units: Units of the original value
    :return: Transfomed value
    """
    try:
        mass_u, heat_u = [s.upper() for s in units.split("_")]
    except:
        msg = "The Units should be o the form X_Y"
        # logging.warning( msg )
        return fuel_emf

    mass_x = mass_factor(mass_u)
    heat_x = heat_factor(heat_u)

    return fuel_emf * mass_x / heat_x


# General Calculations


def calculate_FCF(r, T):
    """
    Calculate FCF from given information
    :param r: Is the rate of inflation
    :param T: Is the time in years
    :return: No units cost factor
    """
    r = r / 100
    den = r * ((1 + r) ** T)
    num = ((1 + r) ** T) - 1
    return den / num


def eff_to_hr(eff):
    """
    Convert electric efficiency into heat rate
    :param eff: Efficiency value, only 0 to 1
    :return: Heat rate as KJ heat/ KWh electricity
    """
    assert 0 <= eff <= 1, "Efficiency out of range"
    return 3600 / eff


def hr_to_eff(hr):
    """
    Converts Heat Rate into efficiency
    :param hr: Heat rate in the form KJ/KWh
    :return: Eff in a unitless value between 0 to 1
    """
    return 3600 / hr


def calc_fuel_emf(plant_emf, heat_rate):
    """
    This is a helper function that calculates emission factors of a power plant into specific factors of the fuels
    it is useful for when the fuel factor is not reported, it only works with the base plants, don't use with capture
    plants as its outputs would not make sense
    :param plant_emf: Emission factor in the form of kgCo2 per KWh
    :param heat_rate: Heat rate in the form of KJ per KWh
    :return: Emission factor as Kg per KJ of Heat produced or ton CO2 per MJ of Heat produced
    """
    return plant_emf / heat_rate


def fom_harmonization(fom, units, power, life):
    """
    Harmonization of Fixed Operation and Management costs
    :param units: Reported units of the data point
    :param power: Power of the powerplant if availible, otherwise None.
    :param life: Lifespan of the powerplant
    :return: Harmonized cost value
    """
    try:
        _, low = [s.upper() for s in units.split("_")]
    except:
        msg = "The Units should be o the form X_Y"
        # logging.warning( msg )
        low = "none"
    if low == "KW":
        return float(fom) / life
    elif low == "KWY":
        return float(fom)
    elif low == "Y":
        return float(fom) / (power * 1000)
    elif low == "none":
        return float(fom) / (life * power * 1000)
    else:
        return fom


def fuel_dimension_match(cost, units, fuel):
    """
    Match the dimensions of reported fuel flows
    :param cost: Reported cost per fuel unit
    :param units: fuel units reported
    :param fuel: name of the fuel
    :return: Harmonized units
    """
    try:
        _, low = [s.upper() for s in units.split("_")]
    except:
        msg = "The Units should be o the form X_Y"
        # logging.warning( msg )
        return cost

    if low == "TON":
        if fuel == "illinois_6":
            return cost / illinois_6_HHV
        elif fuel == "Lignite":
            return cost / lignite_HHV
        elif fuel == "Bituminous":
            return cost / bit_HHV
        else:
            return cost / lignite_HHV

    elif low == "MMBTU":
        return cost / MMBTU_to_GJ
    else:
        return cost


def fuel_name_matching(name, blacks, browns, petcoke):
    """
    Harmonize fuel names
    :param name: Original name
    :param blacks: Hard coal name map
    :param browns: Lignite and brown coal name map
    :param petcoke: Other fuels map
    :return: Harmonized name
    """
    if name in blacks:
        return "Hard Coal"
    elif name in browns:
        return "Lignite"
    elif name in petcoke:
        return "Petcoke"
    elif name == "natural_gas":
        return "Natural Gas"


def HHV_to_LHV(value, ref_HHV, ref_LHV, reverse=False):
    """
    Transfrom values with fuel heat components, This is not a proper transformation ,
    it assumes that the fuel that we are transforming has the properties of the reference fuel used
    :param value: Heat value to be transformed
    :param ref_HHV: HHV of the reference fuel
    :param ref_LHV: LHV of the reference fuel
    :param reverse: If true it will vturn LHV into HHV
    :return:
    """
    if reverse:
        return value * ref_HHV / ref_LHV
    else:
        return value * ref_LHV / ref_HHV
