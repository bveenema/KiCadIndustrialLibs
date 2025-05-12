# KiCad Industrial Libraries  
Schematic symbol libraries for industrial panel design.  

This is a collection of libraries intended for designing Industrial Control Panels.  

It is neither comprehensive nor complete, as libraries and symbols are added as they necessary or useful.  

Efforts are made to maintain consistency among symbols to ensure they appear cohesive on a schematic. However, there are currently no formal guidelines or rules for creating libraries  

## Atomic vs Non-Atomic Libraries
Definition: Atomic Library - A library in which each symbol represents a unique component. For example, a symbol for a Turck PLC (TBEN-L4-PLC). This contrasts with generic symbols, such as a capacitor, resistor, or terminal block, can represent variety of real components.  

In this repository, both atomic and non-atomic libraries are included. For instance, _Cables_Connectors.lib_ is a non-atomic library, smaller in size and suitable for representing cables and connectors from any supplier. In contrast, _Cables_Connectors-AutomationDirect.lib_ and _Cables_Connectors-McMaster.lib_ are atomic libraries, larger in size and represent part numbers from those suppliers. Atomic libraries have their datasheet and Mfg fields pre-filled, whereas-atomic libraries do not.  
