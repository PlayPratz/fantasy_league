# Copyright (c) 2026, Pratik Nerurkar and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class TeamInFantasySeason(Document):
    @property
    def purse_remaining(self):
        return self.purse_total - self.purse_spent
