

RECEPTIONIST_AGENT_TOOLS = [
    {
        "type": "function",
        "name": "get_business_information",
        "description": "Get comprehensive business information including hours, contact details, location, and general information",
        "parameters": {
            "type": "object",
            "properties": {
                "info_type": {
                    "type": "string",
                    "description": "Type of information requested",
                    "enum": ["general", "contact", "location", "all"]
                }
            },
            "required": ["info_type"]
        }
    },
    {
        "type": "function",
        "name": "get_service_information",
        "description": "Get detailed information about salon services and packages",
        "parameters": {
            "type": "object",
            "properties": {
                "service_type": {
                    "type": "string",
                    "description": "Type of service to get information about",
                    "enum": ["Pedicure & Manicure", "Nail Extension", "Waxing", "Eyebrows", "all_services"]
                }
            },
            "required": ["service_type"]
        }
    },
    {
        "type": "function",
        "name": "check_availability",
        "description": "Check availability for a specific service",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to check availability for"
                },
                "time": {
                    "type": "string",
                    "description": "Time to check availability for"
                },
                "service_type": {
                    "type": "string",
                    "description": "Type of service to check availability for"
                }
            },
            "required": ["date", "time", "service_type"]
        }
    },
    {
        "type": "function",
        "name": "get_customer_information",
        "description": "Get information about a specific customer",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Name of the customer to get information about"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Phone number of the customer to get information about"
                }
            },
            "required": ["customer_phone"]
        }
    },
    {
        "type": "function",
        "name": "book_appointment",
        "description": "Book an appointment for a specific service",
        "parameters": {
            "type": "object",
            "properties": {
                "service_type": {
                    "type": "string",
                    "description": "Type of service to book appointment for"
                },
                "name": {
                    "type": "string",
                    "description": "Name of the client"
                },
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the client",
                    "pattern": "^[0-9]{10}$",
                    "example": "0912345678",
                },
                "service_ids": {
                    "type": "array",
                    "description": "Service ids to book appointment for",
                    "items": {
                        "type": "integer",
                        "description": "Service id"
                    }
                },
                "date": {
                    "type": "string",
                    "description": "Date to book appointment for"
                },
                "time": {
                    "type": "string",
                    "description": "Time to book appointment for"
                },
                "available_time_slot": {
                    "type": "object",
                    "properties": {
                        "start_at": {
                            "type": "string",
                            "description": "Start time of the time slot"
                        },
                        "end_at": {
                            "type": "string",
                            "description": "End time of the time slot"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration of the time slot"
                        },
                        "employee_id": {
                            "type": "integer",
                            "description": "Employee id to book appointment for"
                        }
                    },
                    "description": "Time slot to book appointment for"
                }
            },
            "required": ["service_type", "date", "time", "name", "phone_number", "service_ids", "available_time_slot"]
        }
    },
    {
        "type": "function",
        "name": "look_up_appointment",
        "description": "Get next appointments for a specific client",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the client to look up appointment for, format: 0912345678",
                },
                "date": {
                    "type": "string",
                    "description": "Date of the appointment to look up for, format: 2025-01-01"
                }
            },
            "required": ["phone_number", "date"]
        }
    },
    {
        "type": "function",
        "name": "cancel_appointment",
        "description": "Cancel an appointment for a specific service",
        "parameters": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Phone number of the client"
                },
                "date": {
                    "type": "string",
                    "description": "Date of the appointment to cancel"
                },
                "name": {
                    "type": "string",
                    "description": "Name of the client"
                },
                "service_name": {
                    "type": "string",
                    "description": "Service name to cancel"
                },
                "appointment_id": {
                    "type": "integer",
                    "description": "Appointment id to cancel"
                }
            },
            "required": ["phone_number", "date"]
        }
    }
]
