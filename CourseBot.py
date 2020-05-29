#!/usr/bin/env python3
#================================================================================
'''
    File name: CourseBot.py
    Author: Jazib Dawre <jazibdawre@gmail.com>
    Version: 1.4.0
    Date created: 28/05/2020
    License: MIT License
    Description: This is a webcrawler which indexes https://tricksinfo.net/,
                 extracts the coupon codes and opens the udemy course links.
    Python Version: >= 3.6  (Tested on 3.8.0)
'''
#================================================================================
import time, webbrowser, re, requests
from datetime import date, datetime
from bs4 import BeautifulSoup
#================================================================================
'''Settings

"target_url"    Do not change. This is the base url

"user_agent"    We pretend to be this in stealth mode.
                Use any valid UA string you like

"day_limit"     Course older than this value will be marked expired

"page_limit"    Tricksinfo page number after which courses will be marked
                as expired. Each page has 10 courses.

"min_rating"    Minimum udemy rating below which to discard courses

"min_reviewers"  Minimum number of reviewers below which to discard courses

"sleep_prd"     Time to sleep before sending http requests. Low value makes
                the code runs faster but may overload destination server.
                Too low a value and the server may mistake your requests for 
                a DOS attempt. Your IP may be blocked.

"new_courses"   Wether to consider enrolling in new courses

"stealth"       When enabled the bot will identify as the user-agent defined in
                the settings dictionary (default firefox). The bot will not ask
                for robots.txt file from the server to avoid suspicion.

"open_tab"      Wether to open the final udemy links in the default browser
'''
#================================================================================
settings = {
    "target_url" : "https://tricksinfo.net/page/{no}",
    "user_agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0",
    "day_limit" : 3,
    "page_limit" : 2,
    "min_rating" : 3.7,
    "min_reviewers" : 1,
    "sleep_prd" : 10,
    "new_courses" : True,
    "stealth" : False,
    "open_tab" : True
}

def get_page(url):
        
    try:
        #Sending request
        if settings["stealth"]:
            headers={'User-Agent': settings["user_agent"]}
            response = requests.get(url, headers=headers)
        else:
            robots_url="/".join(url.split('/')[:3])+"/robots.txt"
            if True:    #Add robots.txt check
                response = requests.get(url)
            else:
                print(f"\n Respecting robots.txt, Not permitted to access {url}\n Most likely robots.txt changed at {robots_url}. Update script\n")
                return ""
        #Recieving request
        if response.status_code == 200:
            return response.content.decode('utf-8')
        else:
            print(f"\n Error fetching webpage. Response status: {response.status_code}")
            return ""
    except Exception as e:
        print(f" Error in retrieving webpage: {url}.\n Error is {e}")

def get_all_courses():
    try:
        course_names = open('./processed_courses.txt','r')
        courses_list = course_names.read().split('\n')      #List of all course names that were processed
        courses_list = [course.split(' --- ')[0] for course in courses_list if course != '' and course[0] != '#']
    except IOError:
        course_names = open('./processed_courses.txt','w')
        course_names.write("#List of processed Courses. Comments start with #")
        courses_list = []
    except Exception as e:
        print(f" Error in reading name of last processed course: {e}")
        courses_list = []
    finally:
        course_names.close()
        return courses_list

def write_all_courses(course_names, course_links):

    if len(course_links):
        course_list = open('./processed_courses.txt','a')
        course_list.write(f"\n\n#{date.today()} : Writing {len(course_links)} course details to file")
        for i in range(len(course_links)):
            try:
                course_list.write(f"\n{course_names[i]} --- {course_links[i]}")      #Write course name and link
                flag = 0
            except Exception as e:
                print(f" Error in Writing name and list of last processed course.\n Error is: {e}")
                flag = 1
            if flag == 1 :
                print(f"\n The tab was opened but course details couldn't be added to processed_courses.txt. Please add the next line manually:\n{course_names[i]} --- {course_links[i]}\n")
        print(f"\n Course details written to processed_courses.txt")
        course_list.close()

def clean_course_list(course_names, course_links, all_course_names=None):
    try:
        for i in range(len(course_names)):
            try:
                if all_course_names:
                    if(all_course_names.index(course_names[i])>=0):
                        course_links[i]="Enrolled"
            except ValueError:
                pass    #print(f" Course not Enrolled: {course_names[i]}")       use this for detailed output
            except Exception as e:
                print(f" Error in checking against already enrolled courses for '{course_names[i]}'.\n Error: {e}")
        
        #Removing Enrolled and Expired courses
        try:
            course_names_temp, course_links_temp = zip(*((x, y) for x, y in zip(course_names, course_links) if "Enrolled" not in y and 'Expired' not in y and 'Error' not in y))
            course_names=list(course_names_temp)
            course_links=list(course_links_temp)
        except ValueError:
            course_names, course_links = [], []
        except Exception as e:
            print(f" Error in zip cleaning coursr list.\n Error is: {e}")
    except Exception as e:
        print(f" Error in cleaning course list.\n Error is: {e}")
    finally:
        return course_names, course_links

def get_tricksinfo_links(target_url, day_limit, page_limit=5, no=1):
    
    if no>page_limit:        #Scrape only till page 5
        print(f"\n Page Limit Exceeded. Stopping search")
        return [],[]
    else:
        print(f"")
    
    print(f" Page no:{no}. Fetching Page", end='\r')
    page = get_page(target_url.format(no=no))     #Default Start is homepage
    if page=="":
        print(" Page no:{no}. Stopping search")
        return [],[]
    soup = BeautifulSoup(page, 'html.parser')
    print(f" Page no:{no}. Page Fetched Successfully")

    all_course_names = get_all_courses()
    if not all_course_names:
        all_course_names.append('')
    
    course_names = []
    course_links = []       #Here it stores address of tricksinfo page for that course not the udemy link
    course_dates = []
    flag = []
    stop_flag = 0

    try:
        #Get courses names and page links
        courses = soup.find_all('a', class_="post-thumb")      #Specific selector for the image thumbnail which contains href
        for course in courses:
            if course.get('href'):
                course_links.append(course.get('href'))
            if course.get('aria-label'):
                course_names.append(("]".join(re.sub(r'[^\x00-\x7F]+','-', str((course.get('aria-label')))).split(']')[1:])).strip())     #Gets name, then splits it on ]. Since some names have [2020] in end, join the rest of split sections barring the first
        
        print(f" Page no:{no}. Number of Courses Detected:{len(course_names)}")
        print(f" Page no:{no}. Got course names")

        #Get date of post from url of thumbnail image
        wp_image_urls = soup.find_all('img', class_="wp-post-image")
        for link in wp_image_urls:
            if link.get('src'):
                try:
                    course_dates.append(link.get('src').split('/')[-1].split('_')[1])
                except Exception as e:
                    course_dates.append('error')        #any non int would do. This will trigger the date rectifier
        
        print(f" Page no:{no}. Got course dates")

        #Apparently tricksinfo has random naming styles for their images. Hence setting invalid dates to nearest value
        flag = [0]*len(course_dates)
        try:
            for i in range(len(course_dates)):
                try:
                    if int(course_dates[i]) and course_dates[i][:4] == date.today().strftime("%Y"):    #check Date is from this year
                        flag[i] = 1
                except ValueError:
                    pass    #Date is invalid. Let flag be set to 0
                except IndexError:      #Shouldn't be needed but just in case
                    pass    #Date is invalid. Let flag be set to 0
                except Exception as e:
                    print(f" Date {course_dates[i]} couldn't be resolved.\nError: {e}")
            for i in range(len(course_dates)):
                if flag[i]==0:
                    for j in range(len(course_dates)):
                        if flag[j]==1:
                            course_dates[i] = course_dates[j]
                            break
                        else:
                            course_dates[i] = 20200501      #Random value. aka skip if used as page check reference
        except Exception as e:
            print(f" Error in rectifying dates.\nError: {e}")
        
        print(f" Page no:{no}. Rectified dates of courses")
        
        #Use Date to find course to stop at
        for i in range(len(course_links)):
            if (int(date.today().strftime("%Y%m%d"))-int(course_dates[i])) > day_limit:     #mark rest of entries that are older than day_limit
                stop_flag=1
                break
        if stop_flag:
            for j in range(i,len(course_links)):
                course_links[j] = "Expired"

        print(f" Page no:{no}. Courses older than {day_limit} days are marked as expired")

        #Find last saved course to stop if found
        for course_name in course_names:
            try:
                if (all_course_names[-1] == course_name):
                    print(f" Page no:{no}. Processed course found: {course_name[:41]}..")
                    stop_flag=1
                    break
            except:
                continue        #Error will pop if there is problem in reading names of saved course. We can ignore

        print(f" Page no:{no}. Checked last saved course")

        #Verify if course is already added
        course_names, course_links = clean_course_list(course_names, course_links, all_course_names)

        print(f" Page no:{no}. Cleaned course list")
        print(f" Page no:{no}. Number of courses extracted: {len(course_links)}")

        #Get more links if needed
        if not stop_flag:
            course_names_temp, course_links_temp = get_tricksinfo_links(target_url, day_limit, page_limit, no=no+1)       #Increase by current page no and rerun
            course_links += course_links_temp
            course_names += course_names_temp
        else:
            print(f"\n Stopping search. All non-expired/unenrolled courses indexed")

    except Exception as e:
        print(f"\n Webpage with url: {target_url.format(no=no)} had an error.\nError: {e}\n")
    finally:
        return course_names,course_links

def get_udemy_links(target_url, day_limit, page_limit, sleep_prd):

    course_names, course_links = get_tricksinfo_links(target_url=target_url, day_limit=day_limit, page_limit=page_limit)
    
    button_links =[]

    if len(course_links):
        print(f"")

    for i in range(len(course_links)):
        try:
            if "Enrolled" not in course_links[i] and 'Expired' not in course_links[i]:
                time.sleep(sleep_prd)
                page = get_page(course_links[i])
                soup = BeautifulSoup(page, 'html.parser')
                try:
                    buttons = soup.find_all('a', class_="wp-block-button__link")
                    for button in buttons:
                        if button.get('href'):
                            button_links.append(button.get('href')) 
                    print(f" Extracting Udemy Links: {i+1}/{len(course_links)}",end='\r')
                except Exception as e:
                    button_links.append("Error")
                    print(f"\n Couldn't retrieve link from ENROLL button for {buttons[0]}.\nError: {e}")
            else:
                button_links.append("Error")
        except Exception as e:
            button_links.append("Error")
            print(f"\n Couldn't open '{course_links[i]}'.\n Error is {e}")
    
    if len(course_links):
        print(f"")

    course_names, course_links = clean_course_list(course_names, button_links)
    course_names.reverse()
    course_links.reverse()
    write_all_courses(course_names, course_links)       #Write Details of all processed courses
    return course_names, course_links

def filter_udemy_links(target_url, day_limit, page_limit, min_rating, min_reviewers, new_courses, sleep_prd=5):

    course_names, course_links =  get_udemy_links(target_url=target_url, day_limit=day_limit, page_limit=page_limit, sleep_prd=sleep_prd)
    
    if len(course_links):
        print(f"")

    for i in range(len(course_links)):
        try:
            if "Enrolled" not in course_links[i] and 'Expired' not in course_links[i]:
                time.sleep(sleep_prd)
                page = get_page(course_links[i])
                soup = BeautifulSoup(page, 'html.parser')
                try:
                    #This block works for most cases
                    ratings = soup.find_all('span', class_="tooltip-container")
                    if ratings:
                        try:
                            rating = float(ratings[0].contents[1].get_text())
                            if rating < min_rating :
                                if not new_courses==True and rating==0.0:
                                    course_links[i] = "Expired"
                            else:
                                reviews = soup.find_all('span', class_="tooltip-container")
                                if reviews:
                                    reviewers = int((reviews[0].get_text()).split('(')[1].split(' ')[0].replace(",",""))
                                    if reviewers < min_reviewers:
                                        course_links[i] = "Expired"
                        except ValueError:
                            print(f"\n Udemy Normal Page has changed. Please Update the script\n")
                        except Exception as e:
                            print(f"\n Udemy Normal Page has changed. Please Update the script\n Error is: {e}")

                    #If Udemy opens a lite version of the page(idk why but it does), this will work
                    ratings = soup.find_all('span', attrs={"data-purpose": "rating-number"})
                    if ratings:
                        try:
                            rating = float(ratings[0].get_text())
                            if rating < min_rating :
                                if not new_courses==True and rating==0.0:
                                    course_links[i] = "Expired"
                            else:
                                reviews = soup.find_all('div', attrs={"data-purpose": "rating"})
                                if reviews:
                                    reviewers = int((reviews[0].get_text()).split('(')[1].split(' ')[0].replace(",",""))
                                    if reviewers < min_reviewers:
                                        course_links[i] = "Expired"
                        except ValueError:
                            print(f"\n Udemy Lite Page has changed. Please Update the script\n")
                        except Exception as e :
                            print(f"\n Udemy Lite Page has changed. Please Update the script\n Error is: {e}")
                    print(f" Filtering Udemy Links: {i+1}/{len(course_links)}",end='\r')
                except Exception as e:
                    course_links[i] = "Error"
                    print(f"\n Couldn't read rating from '{course_links[i]}'.\n Error is {e}")
            else:
                course_links[i] = "Error"
        except Exception as e:
            course_links[i] = "Error"
            print(f"\n Couldn't open '{course_links[i]}'.\n Error is {e}")
    
    course_names, course_links = clean_course_list(course_names, course_links)
    return course_names, course_links

def open_tabs(target_url, day_limit, page_limit, min_rating, min_reviewers, new_courses, sleep_prd, open_tab):

    course_names, course_links = filter_udemy_links(target_url=target_url, day_limit=day_limit, page_limit=page_limit, min_rating=min_rating, min_reviewers=min_reviewers, new_courses=new_courses,  sleep_prd=sleep_prd)
        
    if len(course_links):
        print(f"")
        for i in range(len(course_links)):
            try:
                if open_tab:
                    time.sleep(sleep_prd)
                    print(f" Opening Udemy Links: {i+1}/{len(course_links)}",end='\r')
                    webbrowser.open_new(course_links[i])
                else:
                    pass
                    #print(f"\n {course_links[i]}") will print udemy links in terminal. A bit messy so it's kept off
            except Exception as e:
                print(f"\n Error while opening Udemy link in browser.\n Error is: {e}")
        print(f"\n All links opened")
    else:
        print(f"\n No New Courses!")

def main():
    target_url = settings["target_url"]
    open_tab = settings["open_tab"]
    day_limit = settings["day_limit"]
    page_limit = settings["page_limit"]
    min_rating = settings["min_rating"]
    min_reviewers = settings["min_reviewers"]
    new_courses = settings["new_courses"]
    stealth = settings["stealth"]
    sleep_prd = settings["sleep_prd"]

    print(f"""
                             CourseBot v1.4.0
 ==============================================================================
 Github: github.com/jazibdawre/Course-Scraper                       MIT License
 Author: Jazib Dawre <jazibdawre@gmail.com>                 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 ==============================================================================

 Current Preferences:
 Base Url :                      {target_url.format(no="")}
 Stealth Mode :                  {stealth}
 Open Links in Browser :         {open_tab}
 Day Limit :                     {day_limit}
 Page limit :                    {page_limit}
 Minimum Rating :                {min_rating}
 Minimum Reviewers :             {min_reviewers}
 Enroll in new Courses :         {new_courses}
 Sleep Period :                  {sleep_prd}

 Preferences can be changed via the settings dictionary
 """)
    for i in range(10):
        time.sleep(1)
        print(f" Bot will initialize after {9-i} seconds, Press Ctrl+C to quit", end="\r")
    print(f"\n\n Initializing...")

    open_tabs(target_url, day_limit, page_limit, min_rating, min_reviewers, new_courses, sleep_prd, open_tab)

if __name__=='__main__':
    try:
        tic = time.time()
        main()
    except KeyboardInterrupt:
        print("\n\n A Ctrl+C can't stop me you meager mortal")
        for i in range(1,4):
            time.sleep(1)
            print(" (evil laugh)"+ " Ha "*i, end="\r")
        time.sleep(1)
        print("\n An anime type story needs to be written here. If you have any ideas do tell .-.")
        time.sleep(5)
        print(" And yeah the bot has stopped don't worry...")
        time.sleep(3)
        print(" I should probably stop wasting more time")
        time.sleep(3)
    except Exception as e:
        print(f"\n Uncaught Exception propogated out of master.\n Error is {type(e).__name__}: {e}")
    finally:
        toc = time.time()
        print(f"\n Exiting. Bye")
        print(f" ==============================================================================\n CourseBot executed in {toc-tic} seconds")