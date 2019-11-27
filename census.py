import requests
import pandas as pd

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
    
    def __init__(self, census_key, google_key, service='GOOGLE'):
        self.census_key = census_key
        self.google_key = google_key
        self.geolocator = GeoLocator(google_key)
        
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
            'H013008': "7plus_person_household",

            
        }

        # Fetch state renter/owner data from US Census
        # Group H4: https://api.census.gov/data/2010/dec/sf1/groups/H4.html

        fields = ['NAME'] + list(fields_of_interest.keys())

        # Geo query. We are going for the block level, no wildcards
        geo = [f"in=state:{block['STATEFP']}", 
               f"in=county:{block['COUNTYFP']}",
               f"in=tract:{block['TRACTCE']}", 
               f"for=block:{block['BLOCKCE']}"]
        
        df = self.query_census_api(fields_of_interest, geo, dataset=dataset, year=year)
        
        # df = pd.DataFrame(census_response[1:], columns = census_response[0])
        # df = df.rename(fields_of_interest, axis="columns")
        
        return {**df.T[0].to_dict(), **block}
    
    
        
    def details_tract_level(self, address):
        
        block = self.geolocator.get_census_block(address)      

        dataset='acs/acs5'
        year='2017'

        fields_of_interest = {
            'B07001_017E': "Same_house_1_year_ago",
            'B07001_001E': "Total_Population",
            # https://api.census.gov/data/2017/acs/acs5/groups/B19127.html
            'B19127_001E': "Aggregate_Income",             
            'B19126_001E': "Median_Family_Income", 
        }

        # Geo query. We are going for the tract level
        geo = [f"in=state:{block['STATEFP']}", 
               f"in=county:{block['COUNTYFP']}",
               f"for=tract:{block['TRACTCE']}"]

        df = self.query_census_api(fields_of_interest, geo, dataset=dataset, year=year)
        
        # df = pd.DataFrame(census_response[1:], columns = census_response[0])
        # df = df.rename(fields_of_interest, axis="columns")
        
        return {**df.T[0].to_dict(), **block}

    def details_all_tracts(self, STATEFP, COUNTYFP):
        
        dataset='acs/acs5'
        year='2017'

        fields_of_interest = {
            'B07001_017E': "Same_house_1_year_ago",
            'B07001_001E': "Total_Population",
            # https://api.census.gov/data/2017/acs/acs5/groups/B19127.html
            'B19127_001E': "Aggregate_Income",             
            'B19126_001E': "Median_Family_Income", 
        }

        # Geo query. We are going for the tract level
        geo = [f"in=state:{STATEFP}", 
               f"in=county:{COUNTYFP}",
               f"for=tract:*"]

        df = self.query_census_api(fields_of_interest, geo, dataset=dataset, year=year)
        
        # df = pd.DataFrame(census_response[1:], columns = census_response[0])
        # df = df.rename(fields_of_interest, axis="columns")
        
        return df    
    

    def query_census_api(self, fields_of_interest, geo, year='2018', dataset='acs', debug=False):
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
        df = df.rename(fields_of_interest, axis="columns")

        return df