import requests
import pandas as pd
import numpy as np

class GeoLocator:
    
    def __init__(self, google_key):
        self.google_key = google_key

    # See https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/census-geocoder.html
    def census_geocoding(self, address, debug=False):
        
        url = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
        params = {
            "address": address,
            "benchmark" : "Public_AR_Current",
            "format": "json",
            "layers": "all"
        }
        response = requests.get(url, params=params)
        result = response.json()
        if 'result' in result and 'addressMatches' in result['result']:
            if len(result['result']['addressMatches'])>=1:
                result = {
                    "status": "ok",
                    "geo": {
                        "lat": result['result']['addressMatches'][0]['coordinates']['y'],
                        "lon": result['result']['addressMatches'][0]['coordinates']['x']
                    }, 
                    "pretty_address": result['result']['addressMatches'][0]['matchedAddress'],
                }
                if debug:
                    result["raw"]=result
                return result
            
        return {
            "status": "error"
        }
    
        
    def google_maps_api(self, address):
        '''
        Takes as input an address and returns back the first result 
        from the Google Maps API
        '''

        GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'address': address,
            'region': 'usa',
            'key': self.google_key
        }
        response = requests.get(GOOGLE_MAPS_API_URL, params=params)
        results = response.json()

        # Use the first result
        if 'results' in results and len(results['results']) > 0:
            result = results['results'][0]
            return result
        else:
            # We got nothing back
            return None
 

        
    def google_geocoding(self, address, debug=False):
        '''
        Geocodes an address using the Google Maps API
        '''
        google_result = self.google_maps_api(address)
        if google_result == None:
            return {
                "status": "error"
            }
        result = {
            "status": "ok",
            "geo": {
                "lat": google_result['geometry']['location']['lat'], 
                "lon": google_result['geometry']['location']['lng'], 
            }, 
            "pretty_address": google_result['formatted_address'],
            # 
        }
        if debug:
            result["raw"] = google_result
        return result

    # Check https://geo.fcc.gov/api/census/#!/area/get_area for the documentation
    # The area API seems to return more information, consider switching
    def fcc_census_block(self, lat, lon):
        FCC_URL = f'https://geo.fcc.gov/api/census/block/find'
        params = {"latitude": lat, "longitude": lon, "format": "json"}
        response = requests.get(FCC_URL,  params=params)
        data = response.json()
        
        state_FIPS = data['State']['FIPS']
        state_name = data['State']['name']
        state_code = data['State']['code']
        county_FIPS = data['County']['FIPS'][len(state_FIPS):]
        county_name = data['County']['name']
        census_tract = data['Block']['FIPS'][len(state_FIPS)+len(county_FIPS):-4]
        block = data['Block']['FIPS'][-4:]
        
        return {
            "state_name": state_name,
            "state_code": state_code,
            "county_name": county_name,
            "STATEFP": state_FIPS,
            "COUNTYFP": county_FIPS,
            "TRACTCE": census_tract,
            "BLOCKCE": block,
            "BLOCKID": data['Block']['FIPS']
        }        


    def get_census_block(self, address, service='GOOGLE'):
        if service == 'GOOGLE':
            result = self.google_geocoding(address)
        elif service == 'CENSUS':
            result = self.census_geocoding(address)
        else:
            return {
                "status": "error"
            }
           
        block = self.fcc_census_block(result['geo']['lat'], result['geo']['lon'])
        block["input_address"]=address
        block["pretty_address"]=result['pretty_address']
        # block["google_raw"]=result['raw']
        block["lat"]=result['geo']['lat']
        block["lon"]=result['geo']['lon']
        block["status"] = "ok"
        return block  
            
    
    

class Census:
    
    # Full list at https://api.census.gov/data/2017/acs/acs5/variables.json
    acs5_fields_of_interest = {
        'B07001_001E': "Total_Population",
        # B07013_002E: Estimate!!Total!!Householder lived in owner-occupied housing units
        'B07013_002E': 'Owner',
        # B07013_003E: Estimate!!Total!!Householder lived in renter-occupied housing units
        'B07013_003E': 'Renter',
        'B07001_017E': "Same_house_1_year_ago",
        # B07013_005E: Estimate!!Total!!Same house 1 year ago!!Householder lived in owner-occupied housing units"
        'B07013_005E': "Same_house_1_year_ago_owner",
        # B07013_006E: Estimate!!Total!!Same house 1 year ago!!Householder lived in renter-occupied housing units
        'B07013_006E': "Same_house_1_year_ago_renter",
        # B19127_001: Estimate!!Aggregate family income in the past 12 months (in 2017 inflation-adjusted dollars)
        'B19127_001E': "Aggregate_Income",             
        'B19126_001E': "Median_Family_Income", 
        'B25064_001E': 'Median_Gross_Rent',
        'B25103_001E': 'Median_Eeal_Estate_Taxes',
        # Estimate!!Gini Index
        'B19083_001E': 'Gini_Index',
      
        # Income distribution: Cutoff values for quintiles
        'B19080_001E': 'Household_Income_Lowest_Quintile_Upper_Limit',
        'B19080_002E': 'Household_Income_Second_Quintile_Upper_Limit',
        'B19080_003E': 'Household_Income_Third_Quintile_Upper_Limit',
        'B19080_004E': 'Household_Income_Fourth_Quintile_Upper_Limit',
        'B19080_005E': 'Household_Income_Top_5_Percent_Lower_Limit',
        
        # Woman fertility: Estimate!!Total!!Women who had a birth in the past 12 months
        'B13016_002E': 'Women_Gave_Birth_Last_Year',
        'B13016_010E': 'Women_No_Birth_Last_Year',
        
        # Tenure of living        

        'B25038_015E': 'Renter_Moved_in_1979_or_earlier',
        'B25038_014E': 'Renter_Moved_in_1980_to_1989',
        'B25038_013E': 'Renter_Moved_in_1990_to_1999',
        'B25038_012E': 'Renter_Moved_in_2000_to_2009',
        'B25038_011E': 'Renter_Moved_in_2010_to_2014',
        'B25038_010E': 'Renter_Moved_in_2015_or_later',
        
        'B25038_008E': 'Owner_Moved_in_1979_or_earlier',
        'B25038_007E': 'Owner_Moved_in_1980_to_1989',
        'B25038_006E': 'Owner_Moved_in_1990_to_1999',
        'B25038_005E': 'Owner_Moved_in_2000_to_2009',
        'B25038_004E': 'Owner_Moved_in_2010_to_2014',
        'B25038_003E': 'Owner_Moved_in_2015_or_later',
        
        'B11016_002E': 'Family_households',
        'B11016_003E': 'Family_households_2person',
        'B11016_004E': 'Family_households_3person',
        'B11016_005E': 'Family_households_4person',
        'B11016_006E': 'Family_households_5person',
        'B11016_007E': 'Family_households_6person',
        'B11016_008E': 'Family_households_7_or_more',
        
        'B11016_009E': 'NonFamily_households',
        'B11016_010E': 'NonFamily_households_1person',
        'B11016_011E': 'NonFamily_households_2person',
        'B11016_012E': 'NonFamily_households_3person',
        'B11016_013E': 'NonFamily_households_4person',
        'B11016_014E': 'NonFamily_households_5person',
        'B11016_015E': 'NonFamily_households_6person',
        'B11016_016E': 'NonFamily_households_7_or_more',        
        
    }

    
    def __init__(self, census_key, google_key, service='GOOGLE'):
        self.census_key = census_key
        self.google_key = google_key
        self.geolocator = GeoLocator(google_key)
        
    # We will eventually depracate this. The decentennial census gives detailed
    # information at the block level (high degree of granularity) but it does
    # not offer too many variables that we can use.
    def details_block_level(self, address):
        
        block = self.geolocator.get_census_block(address)      

        # Querying the decentennial ("dec") census from year 2010, summary file 1 (sf1)
        dataset='dec/sf1'
        year='2010'
        
        fields_of_interest = {
            # https://api.census.gov/data/2010/dec/sf1/groups/H1.json
            'H001001': "Total_Housing_Units",
            # Skip H2 (urban vs rural)
            # https://api.census.gov/data/2010/dec/sf1/groups/H3.json
            'H003002': "Occupied_Units",  
            'H003003': "Vacant_Units",             
            # 'https://api.census.gov/data/2010/dec/sf1/groups/H4.json
            'H004002': "Units_Owned_Mortgaged", 
            'H004003': "Units_Owned_Free", 
            'H004004': "Units_Rented",
            # Skip H5 (status of vacant units)
            # Skip H6 (race)
            'H010001': "Population",
            # https://api.census.gov/data/2010/dec/sf1/groups/H13.json
            'H013002': "1_person_household",
            'H013003': "2_person_household",
            'H013004': "3_person_household",
            'H013005': "4_person_household",
            'H013006': "5_person_household",
            'H013007': "6_person_household",
            'H013008': "7plus_person_household"       
        }

        # Geo query. We are going for the block level, no wildcards
        geo = [f"in=state:{block['STATEFP']}", 
               f"in=county:{block['COUNTYFP']}",
               f"in=tract:{block['TRACTCE']}", 
               f"for=block:{block['BLOCKCE']}"]
        
        df = self.query_census_api(fields_of_interest, geo, dataset=dataset, year=year)
        
        return {**df.T[0].to_dict(), **block}
    
    def add_computed_variables(self, df):
        df["prob_owner"] = df["Owner"]/df["Total_Population"]
        df["prob_renter"] = df["Renter"]/df["Total_Population"]
        df["prob_move"] = 1-df["Same_house_1_year_ago"]/df["Total_Population"]
        df["prob_move_owner"] = 1-df["Same_house_1_year_ago_owner"]/df["Owner"]
        df["prob_move_renter"] = 1-df["Same_house_1_year_ago_renter"]/df["Renter"]
        df["prob_move_renter"] = 1-df["Same_house_1_year_ago_renter"]/df["Renter"]
        df["aux_women_birth"] = df["Women_No_Birth_Last_Year"]+df["Women_Gave_Birth_Last_Year"]
        df["prob_woman_gave_birth"] = df["Women_Gave_Birth_Last_Year"] / df["aux_women_birth"]
        df["aux_owner_moved"] = df['Owner_Moved_in_1979_or_earlier'] + df['Owner_Moved_in_1980_to_1989'] + df['Owner_Moved_in_1990_to_1999'] + df['Owner_Moved_in_2000_to_2009'] + df['Owner_Moved_in_2010_to_2014'] + df['Owner_Moved_in_2015_or_later']

        df["prob_owner_moved_before1979"] = df['Owner_Moved_in_1979_or_earlier'] / df["aux_owner_moved"]
        df["prob_owner_moved_1980_to_1989"] = df['Owner_Moved_in_1980_to_1989'] / df["aux_owner_moved"]
        df["prob_owner_moved_1990_to_1999"] = df['Owner_Moved_in_1990_to_1999'] / df["aux_owner_moved"]
        df["prob_owner_moved_2000_to_2009"] = df['Owner_Moved_in_2000_to_2009'] / df["aux_owner_moved"]
        df["prob_owner_moved_2010_to_2014"] = df['Owner_Moved_in_2010_to_2014'] / df["aux_owner_moved"]
        df["prob_owner_moved_2015_or_later"] = df['Owner_Moved_in_2015_or_later'] / df["aux_owner_moved"]
        
        df.drop(["aux_women_birth", "aux_owner_moved"], axis='columns', inplace=True)
        
        return df
        
        
    def details_tract_level(self, address, debug=False):
        
        block = self.geolocator.get_census_block(address)      
        dataset='acs/acs5'
        year='2017'

        # Geo query. We are going for the tract level
        geo = [f"in=state:{block['STATEFP']}", 
               f"in=county:{block['COUNTYFP']}",
               f"for=tract:{block['TRACTCE']}"]

        df = self.query_census_api(self.acs5_fields_of_interest, geo, dataset=dataset, year=year, debug=debug)
        df = self.add_computed_variables(df)

        return {**df.T[0].to_dict(), **block}

    def details_all_tracts(self, STATEFP, COUNTYFP):
        
        dataset='acs/acs5'
        year='2017'

        # Geo query. We are going for the tract level. In principle
        # we could got for the block group level as well, but often the 
        # variables of interest are not available at that level of detail
        geo = [f"in=state:{STATEFP}", 
               f"in=county:{COUNTYFP}",
               f"for=tract:*",
               # f"for=block group:*"
              ]

        df = self.query_census_api(self.acs5_fields_of_interest, geo, dataset=dataset, year=year)
        

        df = self.add_computed_variables(df)
        
        for column in df.columns:
            if column in ('NAME', 'state', 'county', 'tract'):
                continue
            df[column+'_percentile'] = df[column].rank(pct=True)        
        
        
        return df    
    

    def query_census_api(self, fields_of_interest, geo, year='2018', dataset='acs/acs5', debug=False):
        fields = ['NAME'] + list(fields_of_interest.keys())
        
        base_url = f'https://api.census.gov/data/{year}/{dataset}?key={self.census_key}&get='
        query = [','.join(fields)]
        for item in geo:
            query.append(item)
        add_url = '&'.join(query)
        url = base_url + add_url
        response = requests.get(url)
        if debug:
            print(response.text)
        data = response.json()
        
        df = pd.DataFrame(data[1:], columns = data[0])
        for column in df.columns.values:
            if column in ('NAME', 'state', 'county', 'tract'):
                continue
            df[column] = pd.to_numeric(df[column], errors='ignore')          

        df = df.rename(fields_of_interest, axis="columns")

        # Replacing missing values with proper NaN
        df = df.replace(to_replace=-666666666,value=np.nan, method=None)
        
        return df