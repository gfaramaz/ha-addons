#!/usr/bin/env python3
"""
Test script for MQTT Discovery functionality
Run this to validate the discovery module before deployment
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'maestro_gateway/rootfs/maestro'))

from discovery import DiscoveryManager, ENTITY_DESCRIPTORS
import json

# Mock MQTT client for testing
class MockMQTTClient:
    def __init__(self):
        self.published_messages = []
    
    def publish(self, topic, payload, retain=False):
        self.published_messages.append({
            'topic': topic,
            'payload': payload,
            'retain': retain
        })
        print(f"MQTT Publish: {topic} -> {payload[:100]}{'...' if len(payload) > 100 else ''}")

def test_discovery():
    # Test configuration
    config = {
        '_MQTT_DISCOVERY_ENABLED': True,
        '_MQTT_DISCOVERY_PREFIX': 'homeassistant',
        '_DEVICE_NAME': 'Test MCZ Maestro Stove',
        '_DEVICE_ID': 'test_mcz_stove',
        '_MQTT_TOPIC_PUB': 'Maestro/State',
        '_MQTT_TOPIC_SUB': 'Maestro/Command',
        '_VERSION': '2.11'
    }
    
    # Initialize discovery manager
    mock_client = MockMQTTClient()
    discovery_manager = DiscoveryManager(mock_client, config)
    
    print("🔍 Testing MQTT Discovery Module")
    print(f"Discovery Enabled: {discovery_manager.discovery_enabled}")
    print(f"Device Name: {discovery_manager.device_name}")
    print(f"Device ID: {discovery_manager.device_id}")
    print(f"Total Entities: {len(ENTITY_DESCRIPTORS)}")
    
    # Test device info
    device_info = discovery_manager.get_device_info()
    print(f"Device Info: {json.dumps(device_info, indent=2)}")
    
    # Test entity configurations
    print(f"\n📋 Entity Configurations:")
    for i, entity in enumerate(ENTITY_DESCRIPTORS[:5]):  # Show first 5
        config = discovery_manager.build_entity_config(entity)
        print(f"{i+1}. {entity.friendly_name} ({entity.component_type})")
        print(f"   Topic: {config.get('state_topic', 'N/A')}")
        print(f"   Command: {config.get('command_topic', 'N/A')}")
    
    print(f"... and {len(ENTITY_DESCRIPTORS) - 5} more entities")
    
    # Test discovery config publishing
    print(f"\n📤 Publishing Discovery Configs...")
    discovery_manager.publish_discovery_configs()
    
    # Test availability
    print(f"\n🟢 Testing Availability...")
    discovery_manager.publish_availability_online()
    discovery_manager.publish_availability_offline()
    
    print(f"\n✅ Test Complete!")
    print(f"Total MQTT messages published: {len(mock_client.published_messages)}")
    
    # Show example discovery topics
    print(f"\n📨 Example Discovery Topics:")
    for msg in mock_client.published_messages[:3]:
        print(f"   {msg['topic']}")

if __name__ == "__main__":
    test_discovery()