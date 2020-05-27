import time, requests, webbrowser, html, re
from datetime import date
from bs4 import BeautifulSoup

#Settings
settings = {
    "target_url" : "https://tricksinfo.net/page/{no}",
    "day_limit" : 2,
    "page_limit" : 1,
    "sleep_prd" : 10,
    "page_load_wait" : 6
}

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

def write_all_courses(course_name, course_link):
    try:
        course_names = open('./processed_courses.txt','a')
        course_names.write(f"\n{course_name} --- {course_link}")      #Write course name and link
        return 0
    except Exception as e:
        print(f"Error in Writing name and list of last processed course.\nError is: {e}")
        return 1
    finally:
        course_names.close()

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
        ##Somethings wrong here
        # print("got here")
        # print(len(course_names), len(course_links))
        # print(course_names, course_links)
        # course_names_temp, course_links_temp = zip(*((x, y) for x, y in zip(course_names, course_links) if "Enrolled" not in y and 'Expired' not in y))
        # course_names=list(course_names_temp)
        # course_links=list(course_links_temp)
    except Exception as e:
        print(f"\nError in cleaning course list.\nError is: {e}\n{type(e).__name__}\n")
    finally:
        return course_names, course_links

def get_tricksinfo_links(target_url, day_limit, page_limit=5, no=1):
    
    if no>page_limit:        #Scrape only till page 5
        print(f"\nPage Limit Exceeded. Stopping search\n")
        return [],[]
    
    page = requests.get(target_url.format(no=no))     #Default Start is homepage
    soup = BeautifulSoup(page.content, 'html.parser')

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
            print(f"\nStopping search. All non-expired/unenrolled courses indexed\n")

    except Exception as e:
        print(f"\nWebpage with url: {target_url.format(no=no)} had an error.\nError: {e}\n")
    finally:
        return course_names,course_links

def get_udemy_links(target_url, day_limit, page_limit, sleep_prd):

    course_names, course_links = get_tricksinfo_links(target_url=target_url, day_limit=day_limit, page_limit=page_limit)
    
    button_links =[]

    for i in range(len(course_links)):
        try:
            if "Enrolled" not in course_links[i] and 'Expired' not in course_links[i]:
                time.sleep(sleep_prd)
                page = requests.get(course_links[i])     #Default Start is homepage
                soup = BeautifulSoup(page.content, 'html.parser')
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
    
    course_names, course_links = clean_course_list(course_names, course_links)
    return course_names, course_links

def open_tabs(target_url, day_limit, page_limit, sleep_prd):

    course_names, course_links = get_udemy_links(target_url=target_url, day_limit=day_limit, page_limit=page_limit, sleep_prd=sleep_prd)
    
    course_names.reverse()
    course_links.reverse()
    print(f"\n")
    
    for i in range(len(course_links)):
        try:
            #time.sleep(sleep_prd)
            #webbrowser.open_new(course_links[i])
            response = write_all_courses(course_name=course_names[i], course_link=course_links[i])
            if response == 1 :
                print(f"\nThe tab was opened but course details couldn't be added to processed_courses.txt. Please add the next line manually:\n{course_names[i]} --- {course_links[i]}\n")
            print(f"Opening Udemy Links: {i+1}/{len(course_links)}",end='\r')
        except Exception as e:
            print(f"\nError while opening Udemy link in browser.\nError is: {e}")
    print(f"\nAll links opened and course details written to processed_courses.txt")

def main():
    #Settings
    target_url = settings["target_url"]
    day_limit = settings["day_limit"]
    page_limit = settings["page_limit"]
    sleep_prd = settings["sleep_prd"]
    page_load_wait = settings["page_load_wait"]

    open_tabs(target_url, day_limit, page_limit, sleep_prd)
    
    print(f"\nExiting. Bye")

if __name__=='__main__':
    main()