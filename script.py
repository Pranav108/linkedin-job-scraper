import csv, getopt, sys, requests, re
from bs4 import BeautifulSoup

def main():
    try:
        options, arguments = getopt.getopt(sys.argv[1:], "c:k:d:", ["country=", "keyword=", "database="])
    except getopt.GetoptError as err:
        print(err) # will print something like "option -a not recognized"
        sys.exit(1)
    # script configuration
    country = None
    keyword = None
    csv_database = None
    for option, argument in options:
        if option in ("-c", "--country"):
            country = argument
        elif option in ("-k", "--keyword"):
            keyword = argument
        elif option in ("-d", "--database"):
            csv_database = argument
        else:
            assert False, "invalid option specified"

    # check options
    if country is None:
        assert False, "country must be specified"
    if keyword is None:
        assert False, "keyword must be specified"

    # constants
    csv_header = ['Job ID', 'Title', 'URL', 'Company Name', 'Company Location', 'Date Posted']
    base_url = 'https://www.linkedin.com'
    job_search_url = '/jobs/search?keywords={0}&locationId={1}:0&start={2}'

    # init database as an empty dictionary
    database = {}

    # populate database with existing jobs from csv file 
    if csv_database is not None:
       with open(csv_database, newline='') as csvfile:
            listings = csv.DictReader(csvfile)
            for listing in listings:
                database[int(listing['Job ID'])] = {
                    'Title':listing['Title'],
                    'URL':listing['URL'],
                    'Company Name':listing['Company Name'],
                    'Company Location':listing['Company Location'],
                    'Date Posted':listing['Date Posted'],
                }

    # init the search URL
    start_job_index = 0
    current_url = job_search_url.format(keyword, country, start_job_index)
    last_response_valid = True

    while last_response_valid:
        # fetch current URL
        response = requests.get(base_url + current_url)
        print('fetch:', base_url + current_url, response.status_code)
        if response.status_code != 200:
            print('warning: status code was not 200')
            last_response_valid = False
            break
        
        response = BeautifulSoup(response.text, features="html5lib")

        for job in response('li', class_=re.compile("result-card")) :
            try:
                job_id = job['data-id']
                job_url = job.find('a', class_='result-card__full-card-link')['href'].split('?')[0]
                job_title = job.find('h3').string
                job_company = job.find('h4').string
                job_location = job.find('span', class_="job-result-card__location").string
                job_date_posted = job.find('time')['datetime']
            except:
                print('error: could not parse job information from response')
                last_response_valid = False
                break
            else:
                if job_id not in database:
                    database[job_id] = {
                            'Title':job_title,
                            'URL':job_url,
                            'Company Name':job_company,
                            'Company Location':job_location,
                            'Date Posted':job_date_posted,
                    }
        start_job_index = start_job_index + 25
        current_url = job_search_url.format(keyword, country, start_job_index)


    # write the database back to the file
    if csv_database is None:
        csv_database = 'database' + '-' + keyword + '-' + country + '.csv'
    with open(csv_database, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_header)
        writer.writeheader()
        for job_id, job_desc in database.items():
            writer.writerow({'Job ID':job_id,
                             'Title':job_desc['Title'],
                             'URL':job_desc['URL'],
                             'Company Name':job_desc['Company Name'],
                             'Company Location':job_desc['Company Location'],
                             'Date Posted':job_desc['Date Posted']})


if __name__ == "__main__":
    main()

