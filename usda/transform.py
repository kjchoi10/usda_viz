
import pandas as pd
pd.options.mode.chained_assignment = None # silent pd warnings

class Transform():
    
    def __init__(self):
        self.fruits = pd.read_csv("./fruits/psd_fruits_vegetables.csv")
        self.grains = pd.read_csv("./grains/psd_grains_pulses.csv")
        self.livestock = pd.read_csv("./livestock/psd_livestock.csv")
        self.coffee = pd.read_csv("./coffee/psd_coffee.csv")
        return
    
    def get_commodity_description(self, data: pd.DataFrame):
        """
        Description:
            Gets the unique commodity description for the commoidty dataset to use as an input for transform_commodity_by_year_country_export
        args:
            data: Commodity dataset
        return:
            list: List of unique commodity descriptions for the commodity data
        """
        return list(data['Commodity_Description'].unique())

    def transform_commodity_by_year_country_export(self, data: pd.DataFrame, commodity: str, year: int, filter = True, origin = 'United States, America'):
        """
        Description:
            Transforms the commodity data into specific commodity (ex. 'Meat, Chicken'), year, export, and by default the origin
            from the United States, America,
        args:
            data: ex. livestock
            commodity: ex. 'Meat, Chicken'
            year: 2022
            filter: True results to filtering out zero values
            origin: default set to 'United States, America'
        return:
            Transformed dataset at the commodity, year, country, export level.
        """
        country_year_commodity_yield = data.groupby(['Commodity_Description', 'Country_Name', 'Calendar_Year', 'Attribute_Description'])['Value'].sum().reset_index()
        commodity = country_year_commodity_yield[country_year_commodity_yield['Commodity_Description'] == commodity]
        commodity_by_year = commodity[commodity['Calendar_Year'] == year]
        commodity_by_year_exports = commodity_by_year[commodity_by_year['Attribute_Description'] == 'Exports']
        commodity_by_year_exports['Origin'] = origin
        # Remove any values where there are zeros
        if filter:
            commodity_by_year_exports = commodity_by_year_exports[commodity_by_year_exports['Value'] != 0.0]
        return(commodity_by_year_exports)
    
    def transform_commodity_by_country_export(self, data: pd.DataFrame, filter = True, origin = 'United States, America'):
        """
        Description:
            Transforms the commodity data into specific commodity (ex. 'Meat, Chicken'), year, export, and by default the origin
            from the United States, America. Useful if you wanted to aggregate and sum all the exports to other countries from the origin,
            for all years.
        args:
            data: ex. livestock
            filter: True results to filtering out zero values
            origin: default set to 'United States, America'
        return:
            Transformed dataset at the commodity, country, year export level.
        """
        commodity_yield = data.groupby(['Commodity_Description', 'Country_Name', 'Calendar_Year', 'Attribute_Description'])['Value'].sum().reset_index()
        commodity = commodity_yield[commodity_yield['Attribute_Description'] == 'Exports']
        commodity['Origin'] = origin
        return(commodity.sort_values(by='Calendar_Year'))
    
    def transform_commodity_by_export(self, data: pd.DataFrame, filter = True, origin = 'United States, America'):
        """
        Description:
            Transforms the commodity data into specific commodity (ex. 'Meat, Chicken'), year, export, and by default the origin
            from the United States, America. Useful if you wanted to aggregate and sum all the exports to other countries from the origin,
            for all years.
        args:
            data: ex. livestock
            commodity: ex. 'Meat, Chicken'
            filter: True results to filtering out zero values
            origin: default set to 'United States, America'
        return:
            Transformed dataset at the commodity, year, export level.
        """
        commodity_yield = data.groupby(['Commodity_Description', 'Calendar_Year', 'Attribute_Description'])['Value'].sum().reset_index()
        commodity_yield  = commodity_yield[commodity_yield['Attribute_Description'] == 'Exports']
        commodity_yield['Origin'] = origin
        return(commodity_yield.sort_values(by='Calendar_Year'))