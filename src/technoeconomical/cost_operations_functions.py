import logging


def calc_lcoe_capex(capex, fcf, cf=1, basis="perkw"):
    """
    Calculate capex component of lcoe
    :param capex: Capex in the form of CURR/MW
    :param cf: capacity factor, default is 1
    :param fcf: Plant life cost inflation corrector
    :param basis: Default is per MW, it is there to be open to implement other values
    :return: LCOE CAPEX component in CURR per KWh
    """
    if basis == "perkw":
        capex_lcoe = capex * fcf / (cf * 8760)
    else:
        logging.warning("Currently there is no other basis implemented")
        return None
    return capex_lcoe


def calc_lcoe_om(fom, vom, cf=1):
    """

    :param fom: Fixed operation and maintentance costs as CURR/KWY
    :param vom: Variable cost in the form of CURR/ KWH
    :param cf: Capacity factor assumed for the plant, default is 1
    :return: LCOE O&M component in CURR per KWh
    """
    fixed = fom / (cf * 8600)
    om_lcoe = fixed + vom

    return om_lcoe


def calculate_lcoe_fuel(hr, fc):
    """
    Calculates fuel component of LCOE
    :param hr: Heat rate as KJ/KWH
    :param fc: fuel cost as CURR/GJ
    :return: LCOE fuel component CURR/MWH
    """
    return hr * fc / 1000000


def calculate_emissions(hr, ef, cap_eff=0):
    """
    Calculate emitted and captured carbon
    :param hr: Heat rate as MJ/MWH
    :param ef: Emission factor as Kg/GJ
    :param cap_eff: Unitless
    :return: emission/capture as kg/MWH
    """
    emitted = hr * ef * (1 - cap_eff)
    captured = hr * ef * cap_eff
    return emitted, captured


def cost_of_carbon_capture(lcoe_ref, lcoe_cc, captured):
    return (lcoe_cc - lcoe_ref) / captured
