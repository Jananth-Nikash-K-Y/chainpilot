# ChainPilot MCP

Model Context Protocol server exposing ChainPilot's operational data and
actions as tools for agents.

## Structure
- `server/`    — MCP server bootstrap
- `tools/`     — individual tool implementations
- `prompts/`   — reusable MCP prompt templates
- `resources/` — MCP resource providers (read-only data views)

## Planned tools (not implemented yet)
```
get_truck_status
get_shipment_status
get_inventory_position
get_warehouse_capacity
get_dock_status
get_supplier_performance
get_order_status
find_exceptions
find_stockout_risks
simulate_delay
calculate_recovery_options
recommend_action
validate_action
execute_action
```
