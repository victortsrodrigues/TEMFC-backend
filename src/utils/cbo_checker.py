class CBOChecker:
    """
    Utility class for checking specific terms in CBO (Brazilian Occupational Classification) descriptions.
    """

    @staticmethod
    def contains_terms(cbo_description, terms):
        """
        Checks if all specified terms are present in the CBO description.

        Args:
            cbo_description (str): The CBO description to check.
            terms (list): List of terms to search for.

        Returns:
            bool: True if all terms are found, False otherwise.
        """
        cbo_normalized = cbo_description.upper()
        return all(term.upper() in cbo_normalized for term in terms)

    @staticmethod
    def contains_clinico_terms(cbo_description):
        """
        Checks if the CBO description contains terms related to "Médico Clínico".

        Args:
            cbo_description (str): The CBO description to check.

        Returns:
            bool: True if the description contains "Médico Clínico" terms, False otherwise.
        """
        return any([
            CBOChecker.contains_terms(cbo_description, ["MEDICO", "CLINICO"]),
            CBOChecker.contains_terms(cbo_description, ["MEDICOS", "CLINICO"])
        ])

    @staticmethod
    def contains_generalista_terms(cbo_description):
        """
        Checks if the CBO description contains terms related to "Médico Generalista".

        Args:
            cbo_description (str): The CBO description to check.

        Returns:
            bool: True if the description contains "Médico Generalista" terms, False otherwise.
        """
        return CBOChecker.contains_terms(cbo_description, ["MEDICO", "GENERALISTA"])

    @staticmethod
    def contains_familia_terms(cbo_description):
        """
        Checks if the CBO description contains terms related to "Médico de Família".

        Args:
            cbo_description (str): The CBO description to check.

        Returns:
            bool: True if the description contains "Médico de Família" terms, False otherwise.
        """
        return CBOChecker.contains_terms(cbo_description, ["MEDICO", "FAMILIA"])