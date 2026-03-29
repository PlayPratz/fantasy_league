# Copyright (c) 2026, Pratik Nerurkar and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PlayerinFantasySeason(Document):

    @property
    def recent_points(self):
        return self.points - self.previous_points
