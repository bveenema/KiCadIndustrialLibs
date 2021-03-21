# KiCad Industrial Libraries
Schematic symbol libraries for industrial panel design.

This is a group of libraries used for designing Industrial Control Panels.

It is neither comprehensive, nor complete. Libraries and symbols are added as they are used or needed.

Efforts are made to keep symbols consistent so that they look appropriate when used together on a schematic, however, there is (at this point) no guidelines or rules for creating libraries

## Atomic vs Non-Atomic Libraries
Definition: Atomic Library - A library where every symbol represents a unique component. Example: a symbol for a Turck PLC (TBEN-L4-PLC). This is opposed to generic symbols like a capacitor, resistor, or terminal block. The symbol can be linked to any number of real life devices

In this repository, both atomic and non-atomic libraries exist. A good example would be _Cables_Connectors_ vs _Cables_Connectors_AutomationDirect_ and _Cables_Connectors_McMaster_ the generic _Cables_Connectors_ is non-atomic, much smaller and could be used to represent cables and connectors from any supplier. _Cables_Connectors_AutomationDirect and _Cables_Connectors_McMaster_ are atomic, larger and represent specific part numbers that can be purchased from those supplier. In most cases, atomic libraries will have their datasheet and MPN fields preffilled whereas non-atomic libraries won't
