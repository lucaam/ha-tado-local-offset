"""Config flow for Tado Local Offset integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import homekit_controller
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers import selector

from .const import (
    CONF_BACKOFF_MINUTES,
    CONF_ENABLE_BATTERY_SAVER,
    CONF_ENABLE_PREHEAT,
    CONF_ENABLE_TEMP_DROP_DETECTION,
    CONF_ENABLE_WINDOW_DETECTION,
    CONF_EXTERNAL_TEMP_SENSOR,
    CONF_LEARNING_BUFFER,
    CONF_MAX_PREHEAT_MINUTES,
    CONF_MIN_PREHEAT_MINUTES,
    CONF_ROOM_NAME,
    CONF_TADO_CLIMATE_ENTITY,
    CONF_TADO_DEVICE,
    CONF_TADO_HUMIDITY_SENSOR,
    CONF_TADO_TEMP_SENSOR,
    CONF_TEMP_DROP_THRESHOLD,
    CONF_TOLERANCE,
    CONF_WINDOW_SENSOR,
    DEFAULT_BACKOFF_MINUTES,
    DEFAULT_LEARNING_BUFFER,
    DEFAULT_MAX_PREHEAT_MINUTES,
    DEFAULT_MIN_PREHEAT_MINUTES,
    DEFAULT_TEMP_DROP_THRESHOLD,
    DEFAULT_TOLERANCE,
    DOMAIN,
    MAX_BACKOFF,
    MAX_TOLERANCE,
    MIN_BACKOFF,
    MIN_TOLERANCE,
    TADO_MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)


class TadoLocalOffsetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tado Local Offset."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._data: dict[str, Any] = {}

    @staticmethod
    def _normalize_manufacturer(value: str | None) -> str:
        """Normalize manufacturer string for reliable matching."""
        if not value:
            return ""
        return "".join(char for char in value.lower() if char.isalnum())

    def _is_tado_device(self, device: dr.DeviceEntry) -> bool:
        """Check if selected HomeKit device belongs to Tado."""
        normalized = self._normalize_manufacturer(device.manufacturer)
        return TADO_MANUFACTURER in normalized

    @staticmethod
    def _is_temperature_sensor_entity(entry: er.RegistryEntry) -> bool:
        """Return True if entity registry entry looks like a temperature sensor."""
        if entry.domain != "sensor":
            return False

        device_class = (entry.device_class or "").lower()
        original_device_class = (entry.original_device_class or "").lower()
        if device_class == "temperature" or original_device_class == "temperature":
            return True

        # Fallback for HomeKit entities that miss device_class metadata
        tokens = " ".join(
            filter(
                None,
                [
                    entry.entity_id,
                    entry.original_name,
                    entry.name,
                    entry.unique_id,
                ],
            )
        ).lower()
        return "temperature" in tokens and "humidity" not in tokens

    @staticmethod
    def _is_humidity_sensor_entity(entry: er.RegistryEntry) -> bool:
        """Return True if entity registry entry looks like a humidity sensor."""
        if entry.domain != "sensor":
            return False

        device_class = (entry.device_class or "").lower()
        original_device_class = (entry.original_device_class or "").lower()
        if device_class == "humidity" or original_device_class == "humidity":
            return True

        tokens = " ".join(
            filter(
                None,
                [
                    entry.entity_id,
                    entry.original_name,
                    entry.name,
                    entry.unique_id,
                ],
            )
        ).lower()
        return "humidity" in tokens

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step - room name and device selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store room name
            self._data[CONF_ROOM_NAME] = user_input[CONF_ROOM_NAME]
            self._data[CONF_TADO_DEVICE] = user_input[CONF_TADO_DEVICE]

            # Auto-discover Tado entities from device
            device_registry = dr.async_get(self.hass)
            entity_registry = er.async_get(self.hass)

            device = device_registry.async_get(user_input[CONF_TADO_DEVICE])

            if not device:
                errors["base"] = "device_not_found"
            elif not self._is_tado_device(device):
                errors["base"] = "not_tado_device"
            else:
                # Get all entities for this device
                entities = er.async_entries_for_device(entity_registry, device.id)

                # Find climate entity
                climate_entity = next(
                    (e for e in entities if e.domain == "climate"),
                    None
                )

                # Find temperature sensor
                temp_sensor = next(
                    (e for e in entities
                     if self._is_temperature_sensor_entity(e)),
                    None
                )

                # Find humidity sensor
                humidity_sensor = next(
                    (e for e in entities
                     if self._is_humidity_sensor_entity(e)),
                    None
                )

                if not climate_entity:
                    errors["base"] = "no_climate_entity"
                elif not temp_sensor:
                    errors["base"] = "no_temp_sensor"
                else:
                    # Store discovered entities
                    self._data[CONF_TADO_CLIMATE_ENTITY] = climate_entity.entity_id
                    self._data[CONF_TADO_TEMP_SENSOR] = temp_sensor.entity_id
                    if humidity_sensor:
                        self._data[CONF_TADO_HUMIDITY_SENSOR] = humidity_sensor.entity_id

                    # Store external temp sensor
                    self._data[CONF_EXTERNAL_TEMP_SENSOR] = user_input[CONF_EXTERNAL_TEMP_SENSOR]

                    # Set unique ID
                    await self.async_set_unique_id(
                        f"{DOMAIN}_{user_input[CONF_ROOM_NAME].lower().replace(' ', '_')}"
                    )
                    self._abort_if_unique_id_configured()

                    # Continue to window detection step
                    return await self.async_step_window_detection()

        # Show form
        data_schema = vol.Schema({
            vol.Required(CONF_ROOM_NAME): str,
            vol.Required(CONF_TADO_DEVICE): selector.DeviceSelector(
                selector.DeviceSelectorConfig(
                    integration="homekit_controller",
                )
            ),
            vol.Required(CONF_EXTERNAL_TEMP_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_window_detection(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle window detection configuration."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_battery_saver()

        # Show form
        data_schema = vol.Schema({
            vol.Optional(CONF_ENABLE_WINDOW_DETECTION, default=False): bool,
            vol.Optional(CONF_WINDOW_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor",
                )
            ),
            vol.Optional(CONF_ENABLE_TEMP_DROP_DETECTION, default=False): bool,
            vol.Optional(
                CONF_TEMP_DROP_THRESHOLD,
                default=DEFAULT_TEMP_DROP_THRESHOLD
            ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=3.0)),
        })

        return self.async_show_form(
            step_id="window_detection",
            data_schema=data_schema,
        )

    async def async_step_battery_saver(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle battery saver settings."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_preheat()

        # Show form
        data_schema = vol.Schema({
            vol.Optional(CONF_ENABLE_BATTERY_SAVER, default=True): bool,
            vol.Optional(
                CONF_TOLERANCE,
                default=DEFAULT_TOLERANCE
            ): vol.All(vol.Coerce(float), vol.Range(min=MIN_TOLERANCE, max=MAX_TOLERANCE)),
            vol.Optional(
                CONF_BACKOFF_MINUTES,
                default=DEFAULT_BACKOFF_MINUTES
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_BACKOFF, max=MAX_BACKOFF)),
        })

        return self.async_show_form(
            step_id="battery_saver",
            data_schema=data_schema,
        )

    async def async_step_preheat(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle pre-heat settings."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Cross-field validation
            if user_input.get(CONF_ENABLE_PREHEAT):
                min_preheat = user_input.get(CONF_MIN_PREHEAT_MINUTES, DEFAULT_MIN_PREHEAT_MINUTES)
                max_preheat = user_input.get(CONF_MAX_PREHEAT_MINUTES, DEFAULT_MAX_PREHEAT_MINUTES)
                
                if min_preheat >= max_preheat:
                    errors["base"] = "invalid_preheat_range"
            
            if not errors:
                self._data.update(user_input)

                # Create config entry
                return self.async_create_entry(
                    title=self._data[CONF_ROOM_NAME],
                    data=self._data,
                )

        # Show form
        data_schema = vol.Schema({
            vol.Optional(CONF_ENABLE_PREHEAT, default=False): bool,
            vol.Optional(
                CONF_LEARNING_BUFFER,
                default=DEFAULT_LEARNING_BUFFER
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=50)),
            vol.Optional(
                CONF_MIN_PREHEAT_MINUTES,
                default=DEFAULT_MIN_PREHEAT_MINUTES
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
            vol.Optional(
                CONF_MAX_PREHEAT_MINUTES,
                default=DEFAULT_MAX_PREHEAT_MINUTES
            ): vol.All(vol.Coerce(int), vol.Range(min=30, max=240)),
        })

        return self.async_show_form(
            step_id="preheat",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TadoLocalOffsetOptionsFlow:
        """Get the options flow for this handler.
        
        Args:
            config_entry: The config entry (managed by framework)
            
        Returns:
            The options flow instance
        """
        return TadoLocalOffsetOptionsFlow()


class TadoLocalOffsetOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Tado Local Offset."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values from config entry
        current_tolerance = self.config_entry.options.get(
            CONF_TOLERANCE,
            self.config_entry.data.get(CONF_TOLERANCE, DEFAULT_TOLERANCE)
        )
        current_backoff = self.config_entry.options.get(
            CONF_BACKOFF_MINUTES,
            self.config_entry.data.get(CONF_BACKOFF_MINUTES, DEFAULT_BACKOFF_MINUTES)
        )

        data_schema = vol.Schema({
            vol.Optional(
                CONF_TOLERANCE,
                default=current_tolerance
            ): vol.All(vol.Coerce(float), vol.Range(min=MIN_TOLERANCE, max=MAX_TOLERANCE)),
            vol.Optional(
                CONF_BACKOFF_MINUTES,
                default=current_backoff
            ): vol.All(vol.Coerce(int), vol.Range(min=MIN_BACKOFF, max=MAX_BACKOFF)),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
