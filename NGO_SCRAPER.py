from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
def get_token(sess):
    req_csrf = sess.get('https://ngodarpan.gov.in/index.php/ajaxcontroller/get_csrf')
    return req_csrf.json()['csrf_token']


search_url = "https://ngodarpan.gov.in/index.php/ajaxcontroller/search_index_new/{}"
details_url = "https://ngodarpan.gov.in/index.php/ajaxcontroller/show_ngo_info"

sess = requests.Session()

for page in range(0, 10000, 10):    # Advance 10 at a time
    print(f"Getting results from {page}")

    for retry in range(1, 10):

        data = {
            'state_search' : 27,
            'district_search' : '',
            'sector_search' : 'null',
            'ngo_type_search' : 'null',
            'ngo_name_search' : '',
            'unique_id_search' : '',
            'view_type' : 'detail_view',
            'csrf_test_name' : get_token(sess), 
        }

        req_search = sess.post(search_url.format(page), data=data, headers={'X-Requested-With' : 'XMLHttpRequest'})
        soup = BeautifulSoup(req_search.content, "html.parser")
        table = soup.find('table', id='example')
        df = pd.DataFrame(columns=["Name","city","State", "Address", "Date of Registration","Mobile", "Email", "Website","Members List","Key Issues","Source Of Funds"])
        if table:
            for tr in table.find_all('tr'):
                row = [td.text for td in tr.find_all('td')]
                link = tr.find('a', onclick=True)

                if link:
                    link_number = link['onclick'].strip("show_ngif(')")
                    req_details = sess.post(details_url, headers={'X-Requested-With' : 'XMLHttpRequest'}, data={'id' : link_number, 'csrf_test_name' : get_token(sess)})
                    json = req_details.json()
                    details = json['infor']['0']
                    state = json['infor']['operational_states_db']
                    members = json['member_info']
                    source = []
                    try:
                        source_of_fund = json['source_info']
                        for i in source_of_fund:
                            if i['deptt_name']:
                                source.append(i['deptt_name'] + ", ")

                    except:
                        source = "No Source Fund found for this NGO"

                    if not source:
                        source = "No Source Fund found for this NGO"

                    if type(source) == list:
                        source = " ".join(source)

                    reg=json['registeration_info']
                    city=""
                    address=""
                    for i in reg:
                        city=i["nr_city"]
                        address=i["nr_add"]
                        date_of_reg=i['ngo_reg_date']

                    m_list = []
                    for i in members:
                        if i['MName'] != None:
                            m_list.append(i['FName'] + " " + i['MName'] + ", ")
                        else:
                            m_list.append(i['FName'] + ", ")
                    m_list=" ".join(m_list)
                    website = details['ngo_url']
                    if not website:
                        website = "Not Available"

                    o = ([row[1], city, state, address, date_of_reg, details['Mobile'], details['Email'], website, m_list, row[4], source])
                    df.loc[len(df)] = o
            print(df)
            df.to_csv('NGO_Scraper.csv',mode = "a",header=False, index=False)



            break
        else:
            print(f'No data returned - retry {retry}')
            time.sleep(3)

file = pd.read_csv("NGO_Scraper.csv")
file.to_csv("NGO_Scraper.csv", header=["Name","city","State", "Address", "Date of Registration","Mobile", "Email", "Website","Members List","Key Issues","Source Of Funds"], index=False)