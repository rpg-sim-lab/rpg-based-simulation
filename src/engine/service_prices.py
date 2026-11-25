"""Prices of the town services a subject meets a need with (SURV-06).

A meal at the inn costs gold (SURV-06: "a meal where meals are served, for a price"). Nothing is free (owner decisions 44 and 73): under the ATOMIC payment law
(`service_admission`) a service is delivered only for the full price, taken with the service in one transfer (the debit equals what the payee receives: `conservation.service_price`).
`building_services` charges it and the admission rule reads the same value (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1).
"""
EAT_PRICE_GOLD = 5
REST_PRICE_GOLD = 10
INN_MEAL_HUNGER = 60.0  # the relief of one paid inn meal: the former core 40 plus the inn's 20 (owner decision 73, memo row 73); a src value, on the settings audit list
