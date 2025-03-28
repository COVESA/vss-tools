# Extensions
## Enhancing COVESA VSS with Custom Profile Overlays
Think of these profile overlays as special layers that add depth and functionality to signals, making them smarter and more adaptable. We're talking about profiles like network serialization, cybersecurity, functional safety, and data collection, which are crucial for today's connected vehicles.

### Why Add Overlays?
- Overlays capture and format key data attributes as soon as a signal is created, reducing search time and eliminating the need for custom metadata in various formats.
- They bring all vehicle-related data and specifications into one place, providing system engineers, developers, and analysts with a single source of truth for signals that is both accurate and up-to-date.
- By establishing the relationship between VSS signals and network signals (such as DBC or ARXML), overlays ensure seamless integration from high-level vehicle concepts to network implementations.
- Combining VSS with profiles ensures signals are ready for serialization and implementation, avoiding the current need to maintain separate serialization requirements. This reduces mismatches and the need for custom tools to parse different information sets.

### Profiles
#### Cybersecurity Profile
The cybersecurity profile lets you add security attributes to VSS signals. Refer [Cybersecurity Profile](cybersecurity_profile.md).
#### Network Serialization Profile
The network serialization profile lets you add serialization attributes like update period, init value etc. Refer [Network Serialization Profile](network_serialization_profile.md).


By adding these custom profile overlays, we're not just making the COVESA VSS more flexible and robust, we're also future-proofing it.