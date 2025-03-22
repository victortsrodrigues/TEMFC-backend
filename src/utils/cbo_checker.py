class CBOChecker:
    @staticmethod
    def contains_terms(cbo_description, terms):
        cbo_normalized = cbo_description.upper()
        return all(term.upper() in cbo_normalized for term in terms)

    @staticmethod
    def contains_clinico_terms(cbo_description):
        return any([
            CBOChecker.contains_terms(cbo_description, ["MEDICO", "CLINICO"]),
            CBOChecker.contains_terms(cbo_description, ["MEDICOS", "CLINICO"])
        ])

    @staticmethod
    def contains_generalista_terms(cbo_description):
        return CBOChecker.contains_terms(cbo_description, ["MEDICO", "GENERALISTA"])

    @staticmethod
    def contains_familia_terms(cbo_description):
        return CBOChecker.contains_terms(cbo_description, ["MEDICO", "FAMILIA"])