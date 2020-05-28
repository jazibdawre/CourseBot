#!/usr/bin/env python3
'''
    File name: course_scraper.py
    Author: Jazib Dawre <jazibdawre@gmail.com>
    Date created: 28/05/2020
    Description: This is a webcrawler which indexes https://tricksinfo.net/, extracts the coupon codes and opens the udemy course links.
    Python Version: >= 3.6  (Tested on 3.8.0)
'''

import time, webbrowser, re, urllib.request
from datetime import date
from bs4 import BeautifulSoup

#Settings
settings = {
    "target_url" : "https://tricksinfo.net/page/{no}",
    "user_agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0",
    "open_tab" : True,
    "day_limit" : 1,
    "page_limit" : 5,
    "min_rating" : 3.7,
    "new_courses" : True,
    "sleep_prd" : 10,
    "page_load_wait" : 6
}

def get_page(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': settings["user_agent"]})
        return  urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print(f"Error in retrieving webpage: {url}.\nError is {e}")

def get_all_courses():
    try:
        course_names = open('./processed_courses.txt','r')
        courses_list = course_names.read().split('\n')      #List of all course names that were processed
        courses_list = [course.split(' --- ')[0] for course in courses_list if course != '' and course[0] != '#']
    except IOError:
        course_names = open('./processed_courses.txt','w')
        courses_list = []
    except Exception as e:
        print(f"Error in reading name of last processed course: {e}")
        courses_list = []
    finally:
        course_names.close()
        return courses_list

def write_all_courses(course_names, course_links):

    if len(course_links):
        course_list = open('./processed_courses.txt','a')
        for i in range(len(course_links)):
            try:
                course_list.write(f"\n{course_names[i]} --- {course_links[i]}")      #Write course name and link
                flag = 0
            except Exception as e:
                print(f"\nError in Writing name and list of last processed course.\nError is: {e}")
                flag = 1
            if flag == 1 :
                print(f"\nThe tab was opened but course details couldn't be added to processed_courses.txt. Please add the next line manually:\n{course_names[i]} --- {course_links[i]}\n")
        print(f"\nCourse details written to processed_courses.txt")
        course_list.close()

def clean_course_list(course_names, course_links, all_course_names=None):
    try:
        for i in range(len(course_names)):
            try:
                if all_course_names:
                    if(all_course_names.index(course_names[i])>=0):
                        course_links[i]="Enrolled"
            except ValueError:
                pass    #print(f"Course not Enrolled: {course_names[i]}")       use this for detailed output
            except Exception as e:
                print(f"Error in checking against already enrolled courses for '{course_names[i]}'.\nError: {e}")
        
        #Removing Enrolled and Expired courses
        try:
            course_names_temp, course_links_temp = zip(*((x, y) for x, y in zip(course_names, course_links) if "Enrolled" not in y and 'Expired' not in y and 'Error' not in y))
            course_names=list(course_names_temp)
            course_links=list(course_links_temp)
        except ValueError:
            course_names, course_links = [], []
        except Exception as e:
            print(f"\nError in zip cleaning coursr list.\nError is: {e}")
    except Exception as e:
        print(f"\nError in cleaning course list.\nError is: {e}")
    finally:
        return course_names, course_links

def get_tricksinfo_links(target_url, day_limit, page_limit=5, no=1):
    
    if no>page_limit:        #Scrape only till page 5
        print(f"\nPage Limit Exceeded. Stopping search")
        return [],[]
    
    page = get_page(target_url.format(no=no))     #Default Start is homepage
    soup = BeautifulSoup(page, 'html.parser')

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
        
        print(f"\nPage no:{no}. Number of Courses Detected:{len(course_names)}")
        print(f"Page no:{no}. Got course names")

        #Get date of post from url of thumbnail image
        wp_image_urls = soup.find_all('img', class_="wp-post-image")
        for link in wp_image_urls:
            if link.get('src'):
                try:
                    course_dates.append(link.get('src').split('/')[-1].split('_')[1])
                except Exception as e:
                    course_dates.append('error')        #any non int would do. This will trigger the date rectifier
        
        print(f"Page no:{no}. Got course dates")

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
                    print(f"Date {course_dates[i]} couldn't be resolved.\nError: {e}")
            for i in range(len(course_dates)):
                if flag[i]==0:
                    for j in range(len(course_dates)):
                        if flag[j]==1:
                            course_dates[i] = course_dates[j]
                            break
                        else:
                            course_dates[i] = 20200501      #Random value. aka skip if used as page check reference
        except Exception as e:
            print(f"Error in rectifying dates.\nError: {e}")
        
        print(f"Page no:{no}. Rectified dates of courses")
        
        #Use Date to find course to stop at
        for i in range(len(course_links)):
            if (int(date.today().strftime("%Y%m%d"))-int(course_dates[i])) > day_limit:     #mark rest of entries that are older than day_limit
                stop_flag=1
                break
        if stop_flag:
            for j in range(i,len(course_links)):
                course_links[j] = "Expired"

        print(f"Page no:{no}. Checked dates of course. Courses older than {day_limit} days are marked as expired")

        #Find last saved course to stop if found
        for course_name in course_names:
            try:
                if (all_course_names[-1] == course_name):
                    print(f"Page no:{no}. Last saved course matched: {course_name}")
                    stop_flag=1
                    break
            except:
                continue        #Error will pop if there is problem in reading names of saved course. We can ignore

        print(f"Page no:{no}. Checked last saved course")

        #Verify if course is already added
        course_names, course_links = clean_course_list(course_names, course_links, all_course_names)

        print(f"Page no:{no}. Cleaned course list")
        print(f"Page no:{no}. Number of courses extracted: {len(course_links)}")

        #Get more links if needed
        if not stop_flag:
            course_names_temp, course_links_temp = get_tricksinfo_links(target_url, day_limit, page_limit, no=no+1)       #Increase by current page no and rerun
            course_links += course_links_temp
            course_names += course_names_temp
        else:
            print(f"\nStopping search. All non-expired/unenrolled courses indexed")

    except Exception as e:
        print(f"\nWebpage with url: {target_url.format(no=no)} had an error.\nError: {e}\n")
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
                    print(f"Extracting Udemy Links: {i+1}/{len(course_links)}",end='\r')
                except Exception as e:
                    button_links.append("Error")
                    print(f"\nCouldn't retrieve link from ENROLL button for {buttons[0]}.\nError: {e}")
            else:
                button_links.append("Error")
        except Exception as e:
            button_links.append("Error")
            print(f"\nCouldn't open '{course_links[i]}'.\nError is {e}")

    course_names, course_links = clean_course_list(course_names, button_links)
    write_all_courses(course_names, course_links)       #Write Details of all processed courses
    return course_names, course_links

def filter_udemy_links(target_url, day_limit, page_limit, min_rating, new_courses, sleep_prd=5):

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
                            print(rating)
                            if rating <= min_rating :
                                if not new_courses==True and rating==0.0:
                                    course_links[i] = "Expired"
                        except ValueError:
                            print(f"\nUdemy Normal Page has changed. Please Update the script\n")
                        except Exception as e:
                            print(f"\nUdemy Normal Page has changed. Please Update the script\nError is: {e}")
                    #If Udemy opens a lite version of the page, this will work
                    ratings = soup.find_all('span', attrs={"data-purpose": "rating-number"})
                    if ratings:
                        try:
                            rating = float(ratings[0].get_text())
                            print(rating)
                            if rating <= min_rating :
                                if not new_courses==True and rating==0.0:
                                    course_links[i] = "Expired"
                        except ValueError:
                            print(f"\nUdemy Lite Page has changed. Please Update the script\n")
                        except Exception as e :
                            print(f"\nUdemy Lite Page has changed. Please Update the script\nError is: {e}")
                    print(f"Cleaning Udemy Links: {i+1}/{len(course_links)}",end='\r')
                except Exception as e:
                    course_links[i] = "Error"
                    print(f"\nCouldn't read rating from '{course_links[i]}'.\nError is {e}")
            else:
                course_links[i] = "Error"
        except Exception as e:
            course_links[i] = "Error"
            print(f"\nCouldn't open '{course_links[i]}'.\nError is {e}")
    
    course_names, course_links = clean_course_list(course_names, course_links)
    return course_names, course_links

def open_tabs(target_url, day_limit, page_limit, min_rating, new_courses, sleep_prd, open_tab):

    course_names, course_links = filter_udemy_links(target_url=target_url, day_limit=day_limit, page_limit=page_limit, min_rating=min_rating, new_courses=new_courses,  sleep_prd=sleep_prd)
    
    course_names.reverse()
    course_links.reverse()

    if not open_tab:
        print(f"\nOpening Udemy links in browser has been set to False, this can be changed in the settings dictionary.\nUdemy Links will be printed in terminal")
    
    if len(course_links):
        print(f"")
    else:
        print(f"\nNo New Courses!")
    
    for i in range(len(course_links)):
        try:
            if open_tab:
                time.sleep(sleep_prd)
                print(f"Opening Udemy Links: {i+1}/{len(course_links)}",end='\r')
                webbrowser.open_new(course_links[i])
            else:
                print(f"\n{course_links[i]}")
        except Exception as e:
            print(f"\nError while opening Udemy link in browser.\nError is: {e}")
    print(f"\nAll links opened")

def main():
    #Settings
    target_url = settings["target_url"]
    open_tab = settings["open_tab"]
    day_limit = settings["day_limit"]
    page_limit = settings["page_limit"]
    min_rating = settings["min_rating"]
    new_courses = settings["new_courses"]
    sleep_prd = settings["sleep_prd"]
    page_load_wait = settings["page_load_wait"]

    open_tabs(target_url, day_limit, page_limit, min_rating, new_courses, sleep_prd, open_tab)
    
    print(f"\nExiting. Bye")

if __name__=='__main__':
    main()