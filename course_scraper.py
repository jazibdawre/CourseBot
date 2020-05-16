from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import requests
from datetime import date

def get_all_courses():
    try:
        course_names = open('./processed_courses.txt','r')
        courses_list = course_names.read().split('\n')      #List of all course names that were processed
        course_names.close()
    except IOError:
        course_names = open('./processed_courses.txt','w')
        course_names.close()
        courses_list = []
    except Exception as e:
        print(f"Error in reading name of last processed course: {e}")
        courses_list = []
    finally:
        return courses_list

def clean_course_list(all_course_names, course_names, course_links):
    for i in range(len(course_names)):
        try:
            if(all_course_names.index(course_names[i])>=0):
                course_links[i]="Enrolled"
        except ValueError:
            pass    #print(f"Course not Enrolled: {course_names[i]}")       use this for detailed output
        except Exception as e:
            print(f"Error in checking against already enrolled courses for '{course_names[i]}'.\nError: {e}")
    #Removing Enrolled and Expired courses
    course_names, course_links = zip(*((x, y) for x, y in zip(course_names, course_links) if "Enrolled" not in y and 'Expired' not in y))
    return course_names,course_links

def get_tricksinfo_links(wd, target_url, day_limit, no=1):
    
    wd.get(target_url.format(no=no))     #Default Start is homepage
    
    all_course_names = get_all_courses()
    course_names = []
    course_links = []       #Here it stores address of tricksinfo page for that course not the udemy link
    course_dates = []
    stop_flag = 0
    flag = []

    if no>5:        #Scrape only till page 5
        return course_names,course_links

    try:
        #Get courses names and page links
        courses = wd.find_elements_by_css_selector(".post-thumb")      #Specific selector for the image thumbnail which contains href
        for course in courses:
            if course.get_attribute('href'):
                course_links.append(course.get_attribute('href'))
            if course.get_attribute('aria-label'):
                course_names.append("]".join(course.get_attribute('aria-label').split(']')[1:]))     #Gets name, then splits it on ]. Since some names have [2020] in end, join the rest of split sections barring the first
        
        print(f"\nPage no:{no}. Got course names")

        #Get date of post from url of thumbnail image
        wp_image_urls = wd.find_elements_by_css_selector(".wp-post-image")
        for link in wp_image_urls:
            if link.get_attribute('src'):
                try:
                    course_dates.append(link.get_attribute('src').split('/')[-1].split('_')[1])
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
                except IndexError:      #Shouldn't be needed bt just in case
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
            if (all_course_names[-1] == course_name):
                print(f"Last saved course matched: {course_name}")
                stop_flag=1
                break

        print(f"Page no:{no}. Checked last saved course")

        #Verify if course is already added
        course_names,course_links = clean_course_list(all_course_names, course_names, course_links)

        print(f"Page no:{no}. Cleaned course list")
        print(f"Page no:{no}. Number of courses extracted: {len(course_links)}")

        #Get more links if needed
        if not stop_flag:
            course_names_temp,course_links_temp = get_tricksinfo_links(wd, target_url, day_limit, no=no+1)       #Increase by current page no and rerun
            course_links += course_links_temp
            course_names += course_names_temp
        else:
            print(f"\nStopping search. All non-expired/unenrolled courses indexed")
    except Exception as e:
        print(f"\nWebpage with url: {target_url.format(no=no)} had an error.\nError: {e}")
    finally:
        return course_names,course_links

def get_udemy_links(wd, target_url, day_limit, sleep_prd=1):
    course_names,course_links = get_tricksinfo_links(wd, target_url=target_url, day_limit=day_limit)
    print(f"\nTotal Number of course links recieved:{len(course_links)}\n")
    time.sleep(20)
    for i in range(len(course_links)):
        try:
            #wd.execute_script(f"window.open('{course_links[i]}')")
            print(f"Created new window at {course_links[i]}")
            #time.sleep(10)
            #wd.close()
            #wd.switch_to.window(wd.window_handles[0])
        except Exception as e:
            print(f"\nCouldn't open url for '{course_names[i]}'.\nError is {e}")

def main():
    #Settings
    profile = webdriver.FirefoxProfile(profile_directory="C:\\Users\\home\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\quet6ama.Web-Scraping")
    driver_path = "geckodriver.exe"
    target_url = "https://tricksinfo.net/page/{no}"
    day_limit = 2
    sleep_prd = 1

    with webdriver.Firefox(firefox_profile=profile, executable_path=driver_path) as wd :
        get_udemy_links(wd, target_url=target_url, day_limit=day_limit, sleep_prd=sleep_prd)

if __name__=='__main__':
    main()