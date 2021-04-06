from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

key = secrets.API_KEY
CACHE_FILE_NAME = 'cache.json'
CACHE_DICT = {}

class NationalSite:
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address, zipcode, phone):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone

    def info(self):
        return f"{self.name} ({self.category}): {self.address} {self.zipcode}"

    

def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_url = "https://www.nps.gov"
    response = requests.get(state_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    state_parent = soup.find('ul', class_='dropdown-menu SearchBar-keywordSearch')
    state_list = state_parent.find_all('li', recursive=False)
    state_dict = {}
    for states in state_list:
        state_tag = states.find('a')
        state_name = state_tag.get_text()
        state_link = state_tag['href']
        state_details = state_url + state_link
        if state_name not in state_dict:
            state_dict.update({state_name.lower(): state_details})
    return state_dict

def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    text = make_url_request_using_cache(site_url, CACHE_DICT)
    soup = BeautifulSoup(text, "html.parser")
    header = soup.find(class_="Hero-titleContainer clearfix")
    name = header.find(class_="Hero-title").text.strip()
    category = header.find(class_="Hero-designation").text.strip()
    footer = soup.find(class_="ParkFooter-contact")
    city = footer.find(itemprop="addressLocality").text.strip()
    state = footer.find(itemprop="addressRegion").text.strip()
    zipcode = footer.find(itemprop="postalCode").text.strip()
    phone = footer.find(itemprop="telephone").text.strip()
    address = f"{city}, {state}"

    if category != '':
            category = category
    else:
        category = "no category"

    if city != None and state != None:
        address = city + ", " + state
    else:
        address = ""

    if zipcode != None:
        zipcode = zipcode
    else:
         zipcode = ""

    if phone != None:
        phone = phone
    else:
        phone = ""

    park_instance = NationalSite(name=name, category=category, address=address, zipcode=zipcode, phone=phone)

    return park_instance


def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''

    text = requests.get(state_url).text.strip()
    soup = BeautifulSoup(text, "html.parser")
    parks = soup.find(id="list_parks")
    park_find = parks.find_all(class_="col-md-9 col-sm-9 col-xs-12 table-cell list_left")
    park_list = []
    for park in park_find:
        baseurl = "https://www.nps.gov"
        parameter = park.find("a")["href"]
        url = baseurl + parameter
        site_instance = get_site_instance(url)
        park_list.append(site_instance)
        
    return park_list
    


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    endpoint_url = 'http://www.mapquestapi.com/search/v2/radius'
    params = {'origin': site_object.zipcode, 
    'radius': 10, 
    'maxMatches': 10, 
    "ambiguities": "ignore", 
    "outFormat": "json", 
    'key': key}
    response = requests.get(endpoint_url, params=params)
    results = response.json()
    return results

# Additional Methods for caching 
def load_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None
    
    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache

def save_cache(cache):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it.
    
    Parameters
    ----------
    cache:
        the opened dict
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''

    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()

def make_url_request_using_cache(url, cache):
    '''Check the cache for a saved result for this baseurl+params:values
    combo. If the result is found, return it. Otherwise send a new 
    request, save it, then return it..
    
    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    cache:
        cache file 
    
    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    if (url in cache.keys()):
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        response = requests.get(url)
        cache[url] = response.text 
        save_cache(cache)
        return cache[url]


if __name__ == "__main__":
	CACHE_DICT = load_cache()
	while(True):
		state_input = input('Enter a state name(e.g. Michigan, michigan) or "exit": ')
		if state_input.lower() == 'exit':
			exit()
		else:
			states_url = build_state_url_dict()
			if state_input.lower() in states_url.keys():
				all_states = get_sites_for_state(
                	states_url[state_input.lower()])
				count = 0
				for letter in state_input.lower():
					count += 1
				print('-' * (26 + count))
				print('List of national sites in '+state_input.lower())
				print('-' * (26 + count))
				
				index = 1
				site_dict = {}
				for item in all_states:
					print('['+str(index)+'] '+item.info())
					site_dict[str(index)] = item
					index = index + 1
				
				while(True):
					print()
					number_input = input('Choose the number for detail search or "exit" or "back": ')
					number_input = number_input.lower()
					if number_input =='back':
						break
					elif number_input =='exit':
						exit()
					elif number_input in site_dict.keys():
						nearby_places = get_nearby_places(site_dict[number_input])
						count = 0
						for letter in site_dict[number_input].name:
							count += 1
						print('-' * (12 + count))
						print('Places near '+ site_dict[number_input].name)
						print('-' * (12 + count))
						
					
						for place in nearby_places['searchResults']:
							name = place['name']
							if place['fields']['group_sic_code_name'] == '':
								category = 'no category'
							else:
								category = place['fields']['group_sic_code_name']
							if place['fields']['address'] == '':
								address = 'no address'
							else:
								address = place['fields']['address']
							if place['fields']['city'] == '':
								city = 'no city'
							else:
								city = place['fields']['city']
			
								print("- " + name + " (" + category + "): " + address + ", " + city)
					else:
						print('[Error] Invalid input')
			
	
			else:
				print('[Error] Enter proper state name')
	  
		