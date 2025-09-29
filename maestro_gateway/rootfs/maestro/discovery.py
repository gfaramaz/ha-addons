#!/usr/bin/python3
# coding: utf-8

"""
Home Assistant MQTT Discovery helper for MCZ Maestro Stove

This module provides functionality to automatically discover and configure
the MCZ Maestro stove in Home Assistant using MQTT Discovery.
"""

import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class EntityDescriptor:
    """Describes a Home Assistant entity for MQTT Discovery"""
    def __init__(self, key: str, component_type: str, friendly_name: str, 
                 unit: Optional[str] = None, icon: Optional[str] = None, 
                 device_class: Optional[str] = None, state_class: Optional[str] = None,
                 value_template: Optional[str] = None, command_topic: Optional[str] = None,
                 min_value: Optional[float] = None, max_value: Optional[float] = None,
                 step: Optional[float] = None, mode: Optional[str] = None,
                 payload_on: Optional[str] = None, payload_off: Optional[str] = None):
        self.key = key
        self.component_type = component_type
        self.friendly_name = friendly_name
        self.unit = unit
        self.icon = icon
        self.device_class = device_class
        self.state_class = state_class
        self.value_template = value_template
        self.command_topic = command_topic
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.mode = mode
        self.payload_on = payload_on
        self.payload_off = payload_off


# Entity mapping for all stove sensors and controls
ENTITY_DESCRIPTORS = [
    # Temperature sensors
    EntityDescriptor("Ambient_Temperature", "sensor", "Ambient Temperature", 
                    unit="°C", icon="mdi:thermometer", device_class="temperature", 
                    state_class="measurement"),
    EntityDescriptor("Fume_Temperature", "sensor", "Fume Temperature", 
                    unit="°C", icon="mdi:thermometer", device_class="temperature", 
                    state_class="measurement"),
    EntityDescriptor("Puffer_Temperature", "sensor", "Puffer Temperature", 
                    unit="°C", icon="mdi:thermometer", device_class="temperature", 
                    state_class="measurement"),
    EntityDescriptor("Boiler_Temperature", "sensor", "Boiler Temperature", 
                    unit="°C", icon="mdi:thermometer", device_class="temperature", 
                    state_class="measurement"),
    EntityDescriptor("NTC3_Temperature", "sensor", "NTC3 Temperature", 
                    unit="°C", icon="mdi:thermometer", device_class="temperature", 
                    state_class="measurement"),
    EntityDescriptor("Temperature_Motherboard", "sensor", "Motherboard Temperature", 
                    unit="°C", icon="mdi:thermometer", device_class="temperature", 
                    state_class="measurement"),
    EntityDescriptor("Return_Temperature", "sensor", "Return Temperature", 
                    unit="°C", icon="mdi:thermometer", device_class="temperature", 
                    state_class="measurement"),
    
    # Status sensors
    EntityDescriptor("Stove_State", "sensor", "Stove State", 
                    icon="mdi:fire", value_template="{{ value }}"),
    EntityDescriptor("Power_Level", "sensor", "Power Level", 
                    icon="mdi:fire", state_class="measurement"),
    EntityDescriptor("Fan_State", "sensor", "Fan State", 
                    icon="mdi:fan", state_class="measurement"),
    EntityDescriptor("DuctedFan1", "sensor", "Ducted Fan 1", 
                    icon="mdi:fan", state_class="measurement"),
    EntityDescriptor("DuctedFan2", "sensor", "Ducted Fan 2", 
                    icon="mdi:fan", state_class="measurement"),
    EntityDescriptor("RPM_Fam_Fume", "sensor", "Fume Fan RPM", 
                    unit="rpm", icon="mdi:fan", state_class="measurement"),
    EntityDescriptor("RPM_WormWheel_Set", "sensor", "Auger Set RPM", 
                    unit="rpm", icon="mdi:cog", state_class="measurement"),
    EntityDescriptor("RPM_WormWheel_Live", "sensor", "Auger Live RPM", 
                    unit="rpm", icon="mdi:cog", state_class="measurement"),
    EntityDescriptor("Candle_Condition", "sensor", "Candle Condition", 
                    icon="mdi:candle", state_class="measurement"),
    EntityDescriptor("Brazier", "sensor", "Brazier Status", 
                    icon="mdi:fire"),
    EntityDescriptor("3WayValve", "sensor", "3-Way Valve", 
                    icon="mdi:valve"),
    EntityDescriptor("Pump_PWM", "sensor", "Pump PWM", 
                    unit="%", icon="mdi:pump", state_class="measurement"),
    
    # Information sensors
    EntityDescriptor("Total_Operating_Hours", "sensor", "Total Operating Hours", 
                    icon="mdi:clock", state_class="total_increasing"),
    EntityDescriptor("Hours_To_Service", "sensor", "Hours to Service", 
                    unit="h", icon="mdi:wrench", state_class="measurement"),
    EntityDescriptor("Number_Of_Ignitions", "sensor", "Number of Ignitions", 
                    icon="mdi:fire", state_class="total_increasing"),
    EntityDescriptor("Pellet_Sensor", "sensor", "Pellet Sensor", 
                    icon="mdi:grain"),
    
    # Mode switches
    EntityDescriptor("Power", "switch", "Power", 
                    icon="mdi:power", command_topic=True, 
                    payload_on="1", payload_off="0"),
    EntityDescriptor("Active_Mode", "switch", "Active Mode", 
                    icon="mdi:auto-fix", command_topic=True,
                    payload_on="1", payload_off="0"),
    EntityDescriptor("Eco_Mode", "switch", "Eco Mode", 
                    icon="mdi:leaf", command_topic=True,
                    payload_on="1", payload_off="0"),
    EntityDescriptor("Silent_Mode", "switch", "Silent Mode", 
                    icon="mdi:volume-off", command_topic=True,
                    payload_on="1", payload_off="0"),
    EntityDescriptor("Sound_Effects", "switch", "Sound Effects", 
                    icon="mdi:volume-high", command_topic=True,
                    payload_on="1", payload_off="0"),
    EntityDescriptor("Chronostat", "switch", "Chronostat", 
                    icon="mdi:clock-outline", command_topic=True,
                    payload_on="1", payload_off="0"),
    EntityDescriptor("Control_Mode", "switch", "Control Mode (Manual)", 
                    icon="mdi:gesture-tap-button", command_topic=True,
                    payload_on="1", payload_off="0"),
    EntityDescriptor("AntiFreeze", "switch", "Anti-Freeze", 
                    icon="mdi:snowflake-off", command_topic=True,
                    payload_on="1", payload_off="0"),
    
    # Number controls
    EntityDescriptor("Temperature_Setpoint", "number", "Temperature Setpoint", 
                    unit="°C", icon="mdi:thermometer", command_topic=True,
                    min_value=10, max_value=30, step=0.5, mode="box"),
    EntityDescriptor("Boiler_Setpoint", "number", "Boiler Setpoint", 
                    unit="°C", icon="mdi:thermometer", command_topic=True,
                    min_value=30, max_value=80, step=1, mode="box"),
    EntityDescriptor("Power_Level_Control", "number", "Power Level", 
                    icon="mdi:fire", command_topic=True,
                    min_value=1, max_value=5, step=1, mode="box"),
]


class DiscoveryManager:
    """Manages Home Assistant MQTT Discovery for the MCZ Maestro stove"""
    
    def __init__(self, mqtt_client, config: Dict[str, Any]):
        """
        Initialize the Discovery Manager
        
        Args:
            mqtt_client: MQTT client instance
            config: Configuration dictionary with discovery settings
        """
        self.mqtt_client = mqtt_client
        self.config = config
        self.discovery_enabled = config.get('_MQTT_DISCOVERY_ENABLED', False)
        self.discovery_prefix = config.get('_MQTT_DISCOVERY_PREFIX', 'homeassistant')
        self.device_name = config.get('_DEVICE_NAME', 'MCZ Maestro Stove')
        self.device_id = config.get('_DEVICE_ID', 'mcz_maestro_stove')
        self.base_topic = config.get('_MQTT_TOPIC_PUB', 'Maestro/State').rstrip('/')
        self.command_topic = config.get('_MQTT_TOPIC_SUB', 'Maestro/Command').rstrip('/')
        self.availability_topic = f"{self.base_topic}/availability"
        
        logger.info(f"Discovery Manager initialized. Enabled: {self.discovery_enabled}")
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get device information for Home Assistant discovery"""
        return {
            "identifiers": [self.device_id],
            "name": self.device_name,
            "manufacturer": "MCZ",
            "model": "Maestro Stove",
            "sw_version": self.config.get('_VERSION', '1.0'),
            "suggested_area": "Living Room"
        }
    
    def build_entity_config(self, entity: EntityDescriptor) -> Dict[str, Any]:
        """
        Build MQTT Discovery config payload for an entity
        
        Args:
            entity: EntityDescriptor instance
            
        Returns:
            Configuration dictionary for the entity
        """
        object_id = f"{self.device_id}_{entity.key.lower()}"
        unique_id = f"{self.device_id}-{entity.key}"
        
        config = {
            "name": f"{self.device_name} {entity.friendly_name}",
            "unique_id": unique_id,
            "object_id": object_id,
            "device": self.get_device_info(),
            "availability_topic": self.availability_topic,
            "state_topic": f"{self.base_topic}/{entity.key}",
        }
        
        # Add optional attributes based on entity type
        if entity.unit:
            config["unit_of_measurement"] = entity.unit
        if entity.icon:
            config["icon"] = entity.icon
        if entity.device_class:
            config["device_class"] = entity.device_class
        if entity.state_class:
            config["state_class"] = entity.state_class
        if entity.value_template:
            config["value_template"] = entity.value_template
        
        # Add command topic for controllable entities
        if entity.command_topic:
            # Handle special case for Power_Level_Control
            if entity.key == "Power_Level_Control":
                config["command_topic"] = f"{self.command_topic}/Power_Level"
            else:
                config["command_topic"] = f"{self.command_topic}/{entity.key}"
        
        # Switch-specific payloads
        if entity.component_type == "switch":
            config["payload_on"] = entity.payload_on or "1"
            config["payload_off"] = entity.payload_off or "0"
            config["state_on"] = "1"
            config["state_off"] = "0"
        
        # Number-specific attributes
        if entity.component_type == "number":
            if entity.min_value is not None:
                config["min"] = entity.min_value
            if entity.max_value is not None:
                config["max"] = entity.max_value
            if entity.step is not None:
                config["step"] = entity.step
            if entity.mode:
                config["mode"] = entity.mode
        
        return config
    
    def publish_discovery_configs(self):
        """Publish discovery configurations for all entities"""
        if not self.discovery_enabled:
            logger.debug("MQTT Discovery disabled, skipping config publication")
            return
            
        logger.info("Publishing MQTT Discovery configurations...")
        
        for entity in ENTITY_DESCRIPTORS:
            try:
                config = self.build_entity_config(entity)
                object_id = f"{self.device_id}_{entity.key.lower()}"
                
                # Discovery topic format: <discovery_prefix>/<component>/<node_id>/<object_id>/config
                discovery_topic = f"{self.discovery_prefix}/{entity.component_type}/{self.device_id}/{object_id}/config"
                
                # Publish with retain=True so discovery persists
                self.mqtt_client.publish(discovery_topic, json.dumps(config), retain=True)
                logger.debug(f"Published discovery config for {entity.friendly_name}")
                
            except Exception as e:
                logger.error(f"Failed to publish discovery config for {entity.friendly_name}: {e}")
    
    def publish_availability_online(self):
        """Publish availability status as online"""
        if not self.discovery_enabled:
            return
            
        try:
            self.mqtt_client.publish(self.availability_topic, "online", retain=True)
            logger.debug("Published availability: online")
        except Exception as e:
            logger.error(f"Failed to publish availability online: {e}")
    
    def publish_availability_offline(self):
        """Publish availability status as offline"""
        if not self.discovery_enabled:
            return
            
        try:
            self.mqtt_client.publish(self.availability_topic, "offline", retain=True)
            logger.debug("Published availability: offline")
        except Exception as e:
            logger.error(f"Failed to publish availability offline: {e}")
    
    def cleanup_discovery_configs(self):
        """Remove discovery configurations (publish empty payload)"""
        if not self.discovery_enabled:
            return
            
        logger.info("Cleaning up MQTT Discovery configurations...")
        
        for entity in ENTITY_DESCRIPTORS:
            try:
                object_id = f"{self.device_id}_{entity.key.lower()}"
                discovery_topic = f"{self.discovery_prefix}/{entity.component_type}/{self.device_id}/{object_id}/config"
                
                # Publish empty payload with retain=True to remove the config
                self.mqtt_client.publish(discovery_topic, "", retain=True)
                logger.debug(f"Removed discovery config for {entity.friendly_name}")
                
            except Exception as e:
                logger.error(f"Failed to remove discovery config for {entity.friendly_name}: {e}")