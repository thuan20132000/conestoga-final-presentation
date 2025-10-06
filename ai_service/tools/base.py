from typing import Dict, Any, List


class BaseTool:
    """Base tool class."""

    def __init__(self):
        """Initialize the base tool."""
        pass

    async def business_knowledge_base(self) -> Dict[str, Any]:
        """Get the business knowledge base."""
        BUSINESS_KNOWLEDGE_BASE = {
            "business_info": {
                "name": "SnapsBooking Salon",
                "phone": "(555) 123-4567",
                "email": "info@snapsbooking.com",
                "website": "www.snapsbooking.com",
                "address": "123 Salon Lane, Creative District, City, State 12345",
                "established": "2020"
            },
            "services": {
                "full_set": {
                    "description": "Professional full set sessions for individuals and families",
                    "duration": "1-3 hours",
                    "starting_price": "$55",
                    "includes": [
                        "Professional editing",
                        "Digital gallery",
                        "Print options"
                    ],
                    "available_days": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "available_times": [
                        "9:00 AM to 12:00 PM"
                    ]
                },
                "fill": {
                    "description": "Professional filler sessions for individuals and families",
                    "duration": "1 hour",
                    "starting_price": "$35",
                    "includes": [
                        "Professional editing",
                        "Digital gallery",
                        "Print options"
                    ],
                    "available_days": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "available_times": [
                        "9:00 AM",
                        "10:00 AM",
                        "11:00 AM",
                        "12:00 PM",
                        "1:00 PM",
                        "2:00 PM",
                        "3:00 PM",
                        "4:00 PM",
                        "5:00 PM",
                        "6:00 PM",
                        "7:00 PM",
                        "8:00 PM",
                        "9:00 PM",
                        "10:00 PM"
                    ]
                },
                "pedicure": {
                    "description": "Professional pedicure sessions for individuals and families",
                    "duration": "1 hour",
                    "starting_price": "$35",
                    "includes": [
                        "Professional editing",
                        "Digital gallery",
                        "Print options"
                    ],
                    "available_days": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "available_times": [
                        "9:00 AM",
                        "10:00 AM",
                        "11:00 AM",
                        "12:00 PM",
                        "1:00 PM",
                        "2:00 PM",
                        "3:00 PM",
                        "4:00 PM",
                        "5:00 PM",
                        "6:00 PM",
                        "7:00 PM",
                        "8:00 PM",
                        "9:00 PM",
                        "10:00 PM"
                    ]
                },
                "manicure": {
                    "description": "Professional manicure sessions for individuals and families",
                    "duration": "1 hour",
                    "starting_price": "$35",
                    "includes": [
                        "Professional editing",
                        "Digital gallery",
                        "Print options"
                    ],
                    "available_days": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "available_times": [
                        "9:00 AM",
                        "10:00 AM",
                        "11:00 AM",
                        "12:00 PM",
                        "1:00 PM",
                        "2:00 PM",
                        "3:00 PM",
                        "4:00 PM",
                        "5:00 PM",
                        "6:00 PM",
                        "7:00 PM",
                        "8:00 PM",
                        "9:00 PM",
                        "10:00 PM"
                    ]
                },
                "waxing": {
                    "description": "Professional waxing sessions for individuals and families",
                    "duration": "1 hour",
                    "starting_price": "$35",
                    "includes": [
                        "Professional editing",
                        "Digital gallery",
                        "Print options"
                    ],
                    "available_days": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "available_times": [
                        "9:00 AM",
                        "10:00 AM",
                        "11:00 AM",
                        "12:00 PM",
                        "1:00 PM",
                        "2:00 PM",
                        "3:00 PM",
                        "4:00 PM",
                        "5:00 PM",
                        "6:00 PM",
                        "7:00 PM",
                        "8:00 PM",
                        "9:00 PM",
                        "10:00 PM"
                    ]
                }
            },
            "hours": {
                "monday": "9:30 AM - 7:30 PM",
                "tuesday": "9:30 AM - 7:30 PM",
                "wednesday": "9:30 AM - 7:30 PM",
                "thursday": "9:30 AM - 7:30 PM",
                "friday": "9:30 AM - 7:30 PM",
                "saturday": "9:30 AM - 6:00 PM",
                "sunday": "10:00 AM - 5:00 PM"
            },
            "packages": {
                "full_set": {
                    "description": "Professional full set sessions for individuals and families",
                    "duration": "1-3 hours",
                    "starting_price": "$55",
                    "includes": [
                        "Professional editing",
                        "Digital gallery",
                        "Print options"
                    ],
                    "available_days": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "available_times": [
                        "9:00 AM to 12:00 PM"
                    ]
                },
                "fill": {
                    "description": "Professional filler sessions for individuals and families",
                    "duration": "1 hour",
                    "starting_price": "$35",
                    "includes": [
                        "Professional editing",
                        "Digital gallery",
                        "Print options"
                    ],
                    "available_days": [
                        "Monday",
                        "Tuesday",
                        "Wednesday",
                        "Thursday",
                        "Friday",
                        "Saturday",
                        "Sunday"
                    ],
                    "available_times": [
                        "9:00 AM",
                        "10:00 AM",
                        "11:00 AM",
                        "12:00 PM",
                        "1:00 PM",
                        "2:00 PM",
                        "3:00 PM",
                        "4:00 PM",
                        "5:00 PM",
                        "6:00 PM",
                        "7:00 PM",
                        "8:00 PM",
                        "9:00 PM",
                        "10:00 PM"
                    ]
                }
            },
            "policies": {
                "booking": "50% deposit required to secure booking",
                "cancellation": "48-hour cancellation policy for rescheduling",
                "payment": "We accept cash, credit cards, and payment plans",
                "delivery": "Photos delivered within 2-3 weeks via online gallery"
            }
        }
        
        return BUSINESS_KNOWLEDGE_BASE

    async def get_agent_tools(self) -> List[Dict[str, Any]]:
        """Get the agent tools."""
        agent_tools = [
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
                            "enum": ["full_set", "filler", "pedicure", "manicure", "waxing", "hair_cut", "all_services"]
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
        ]
        
        return agent_tools
