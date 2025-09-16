from shiny import App, ui, render, reactive, run_app
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns 
import os

ui.input_slider("n", "N", 0, 100, 20)

# Set style for matplotlib
plt.style.use('ggplot')

# Constants
POPULATION_COL = 'B01003_001E'
RACE_COLS = [
    'B02001_002E',  # White alone
    'B02001_003E',  # Black or African American alone
    'B02001_004E',  # American Indian and Alaska Native alone
    'B02001_005E',  # Asian alone
    'B02001_006E',  # Pacific Islander alone
    'B02001_007E',  # Other Race alone
    'B02001_008E',  # Two or more races
    'B02001_009E',  # Two races including Some other race
    'B02001_010E'   # Two races excluding Some other race
]

RACE_LABELS = {
    
    'B02001_002E': 'White',
    'B02001_003E': 'Black/African American',
    'B02001_004E': 'American Indian/Alaska Native',
    'B02001_005E': 'Asian',
    'B02001_006E': 'Pacific Islander',
    'B02001_007E': 'Other Race',
    'B02001_008E': 'Two or More Races',
    'B02001_009E': 'Two Races (incl. Other)',
    'B02001_010E': 'Two Races (excl. Other)'
}

def load_and_prepare_data(file_path):
    """Load and prepare the census data."""
    try:
        df = pd.read_csv(file_path)
        
        # Rename columns
        numeric_cols = [POPULATION_COL] + RACE_COLS
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {str(e)}")

# Load the dataset
try:
    df = load_and_prepare_data("census_acs5_all_states_2009_2023.csv")
except Exception as e:
    print(f"Error: {e}")
    df = pd.DataFrame()

# UI Layout 
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .chart-container-line { width: 100%; height: auto; border: 5px solid #ddd; border-radius: 5px; padding:1em; margin-bottom: 2rem;  overflow: hidden; }
            .chart-container-bar {margin-bottom: 2em; border: 5px solid #ddd; padding: 1em; border-radius: 5px;}
            .chart-container-table {margin-bottom: 2em; border: 5px solid #ddd; padding: 1em; border-radius: 5px;}
            .sidebar { padding: 1em; background-color: #f8f9fa; border-right: 1px solid #dee2e6; }
            .main-content { padding: 1em; }
            .header { background-color: #f8f9fa; padding: 1em; margin-bottom: 2em; border-bottom: 1px solid #dee2e6; }
        """)
    ),
    ui.div(
        {"class": "header"},
        ui.h1("US Census Demographics Dashboard (2009-2023) Based On acs5 Survey", class_="text-center"),
        ui.p("Explore population demographics across US states over time", class_="text-center text-muted")
    ),
    ui.row(
        ui.column(3,
            ui.div(
                {"class": "sidebar"},
                ui.h4("Data Controls"),
                ui.input_select(
                    "year",
                    "Select Year:",
                    choices=sorted(df['YEAR'].unique().astype(str)),
                    selected=str(df['YEAR'].max())
                ),
                ui.input_select(
                    "state",
                    "Select State:",
                    choices=sorted(df['NAME'].unique())
                ),
                ui.hr(),
                ui.input_checkbox_group(
                    "race_selection",
                    "Select Demographics:",
                    choices=list(RACE_LABELS.values()),
                    selected=list(RACE_LABELS.values())[:6]
                ),
                ui.hr(),
                ui.div(
                    ui.h4("State Statistics"),
                    ui.output_text("total_population"),
                    ui.output_text("state_percentage")
                ),
                ui.hr(),
                ui.download_button("download", "Download State Data")
            )
        ),
        ui.column(9,
            ui.div(
                {"class": "main-content"},
                ui.div(
                    {"class": "chart-container-line"},
                    ui.h3("Population Trend Over Time"),
                    ui.output_plot("line_chart")
                ),
                ui.div(
                    {"class": "chart-container-bar"},
                    ui.h3("Demographic Distribution"),
                    ui.output_plot("bar_chart")
                ),
                ui.div(
                    {"class": "chart-container-table"},
                    ui.h3("Detailed Demographic Data"),
                    ui.output_data_frame("table")
                )
            )
        )
    )
)

# Server Logic
def server(input, output, session):
    @reactive.Calc
    def filtered_data():
        return df[(df["YEAR"] == int(input.year())) & 
                 (df["NAME"] == input.state())]
    
    # Text outputs
    @output
    @render.text
    def total_population():
        data = filtered_data()
        if not data.empty:
            pop = data[POPULATION_COL].iloc[0]
            return f"Total Population: {pop:,.0f}"
        return "No data available"
    
    @output
    @render.text
    def state_percentage():
        data = filtered_data()
        if not data.empty:
            total_us_pop = df[df["YEAR"] == int(input.year())][POPULATION_COL].sum()
            state_pop = data[POPULATION_COL].iloc[0]
            percentage = (state_pop / total_us_pop) * 100
            return f"% of US Population: {percentage:.2f}%"
        return ""

    # Table
    @output
    @render.data_frame
    def table():
        data = filtered_data()
        if not data.empty:
            display_data = pd.DataFrame({
                'Category': ['Total Population'] + list(RACE_LABELS.values()),
                'Population': [data[POPULATION_COL].iloc[0]] + 
                            [data[col].iloc[0] for col in RACE_COLS],
                'Percentage': [100.0] + 
                            [(data[col].iloc[0] / data[POPULATION_COL].iloc[0] * 100) 
                             for col in RACE_COLS]
            })
            display_data['Percentage'] = display_data['Percentage'].round(2)
            display_data['Population'] = display_data['Population'].apply(lambda x: f"{x:,.0f}")
            display_data['Percentage'] = display_data['Percentage'].apply(lambda x: f"{x:.1f}%")
            return display_data
        return pd.DataFrame()

    # plot outputs
    @output
    @render.plot
    def line_chart():
        state_data = df[df['NAME'] == input.state()].copy()
        if not state_data.empty:
            fig = Figure(figsize=(12, 6))
            ax = fig.add_subplot(111)
            
            ax.plot(state_data['YEAR'], state_data[POPULATION_COL], 
                   marker='o', linewidth=1, color='r')
            
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            
            ax.set_title(f'Population Trend in {input.state()}')
            ax.set_xlabel('Year')
            ax.set_ylabel('Population')
            ax.grid(True, alpha=0.9)
            

            #
            state_data['Smoothed'] = state_data[POPULATION_COL].rolling(window=2, center=True).mean()
            ax.plot(state_data['YEAR'], state_data['Smoothed'], 
            linestyle='--', linewidth=2, color='blue', label='Smoothed Trend')
            ax.legend()

            


           
            return fig
    
    @output
    @render.plot
    def bar_chart():
        data = filtered_data()
        if not data.empty:
            selected_races = {k: v for k, v in RACE_LABELS.items() 
                            if v in input.race_selection()}
            
            populations = [data[col].iloc[0] for col in selected_races.keys()]
            labels = list(selected_races.values())
            percentages = [(pop / data[POPULATION_COL].iloc[0]) * 100 for pop in populations]
            
            fig = Figure(figsize=(14, 4))
            ax = fig.add_subplot(111)
            
            bars = ax.bar(labels, populations, color='#007bff')
            
            for bar, percentage in zip(bars, percentages):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{percentage:.1f}%',
                       ha='center', va='bottom')
            
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            
            ax.set_title(f'Demographic Distribution in {input.state()} ({input.year()})')
            ax.set_xlabel('Demographic Group')
            ax.set_ylabel('Population')
            plt.setp(ax.get_xticklabels(), rotation=10, ha='right')
            ax.grid(True, alpha=0.3)

            fig.text(0.99,0.01, 'Data Source: acs5', ha='right', va='bottom', fontsize=10, color='#999999')
            
            
            return fig


    # Download handler
    @session.download(filename=lambda: f"state_data_{input.state()}_{input.year()}.csv")
    def download():
        data = filtered_data()
        if not data.empty:
            column_labels = {'B01003_001E': 'Total Population', **RACE_LABELS}
            # Prepare the data
            download_data = data.copy()
            download_data = download_data.rename(columns=column_labels)

            # Create a CSV in memory
            csv_buffer = io.StringIO()
            download_data.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)

            # Yield CSV content
            yield csv_buffer.getvalue()
        else:
            yield "No data available for the selected state and year."


app = App(app_ui, server)

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 8000))  # Default to 8000 locally
#     run_app(app, port=port, host="0.0.0.0")
