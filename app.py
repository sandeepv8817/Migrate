# app.py (Streamlit Web UI for Azure Resource Scanner)

import streamlit as st
import json
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

st.set_page_config(layout="wide")

st.title("Azure Resource Scanner - Web Viewer")

# Load resources.json
resources_file = Path("resources.json")
graph_file = Path("dependencies.gml")

if not resources_file.exists():
    st.error("resources.json not found. Run the scanner first.")
    st.stop()

with open(resources_file) as f:
    resources = json.load(f)

# Filters
all_types = sorted(set(r["type"] for r in resources))
all_locations = sorted(set(r["location"] for r in resources))
all_groups = sorted(set(r["resourceGroup"] for r in resources))

st.sidebar.header("🔎 Filters")
type_filter = st.sidebar.multiselect("Resource Type", all_types)
location_filter = st.sidebar.multiselect("Location", all_locations)
group_filter = st.sidebar.multiselect("Resource Group", all_groups)
show_unused = st.sidebar.checkbox("Only show unused resources", False)

# Filter logic
filtered = []
for r in resources:
    if type_filter and r["type"] not in type_filter:
        continue
    if location_filter and r["location"] not in location_filter:
        continue
    if group_filter and r["resourceGroup"] not in group_filter:
        continue
    if show_unused and not r.get("unused"):
        continue
    filtered.append(r)

# Table view
st.subheader(f"📋 Displaying {len(filtered)} of {len(resources)} resources")
df = pd.DataFrame(filtered)
st.dataframe(df, use_container_width=True)

# CSV download
st.download_button(
    label="Download CSV",
    data=df.to_csv(index=False).encode('utf-8'),
    file_name="azure_resources.csv",
    mime="text/csv"
)

# Graph view
if graph_file.exists():
    G = nx.read_gml(graph_file)
    st.subheader("🧩 Resource Dependency Graph")

    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_size=800, node_color="#9ecae1", font_size=8, edge_color="#636363", ax=ax)
    st.pyplot(fig)
else:
    st.warning("Dependency graph not found. Run the scanner to generate dependencies.gml.")

"""
Terraform Template to Deploy the Streamlit App on Azure App Service (Linux Container)
"""

# Save this separately as `main.tf`
terraform_config = """
provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "scanner" {
  name     = "azure-scanner-rg"
  location = "East US"
}

resource "azurerm_app_service_plan" "scanner_plan" {
  name                = "scanner-service-plan"
  location            = azurerm_resource_group.scanner.location
  resource_group_name = azurerm_resource_group.scanner.name
  kind                = "Linux"

  sku {
    tier = "Basic"
    size = "B1"
  }

  reserved = true
}

resource "azurerm_app_service" "scanner_app" {
  name                = "azure-scanner-web"
  location            = azurerm_resource_group.scanner.location
  resource_group_name = azurerm_resource_group.scanner.name
  app_service_plan_id = azurerm_app_service_plan.scanner_plan.id

  site_config {
    linux_fx_version = "DOCKER|streamlit/streamlit"
  }

  app_settings = {
    WEBSITES_PORT = "8501"
  }
}
"""

with open("main.tf", "w") as tf:
    tf.write(terraform_config)

st.success("Terraform configuration saved as 'main.tf'")
