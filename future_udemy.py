
def filter_udemy_links(wd, target_url, day_limit, page_limit, sleep_prd=5):
    course_names, course_links =  get_udemy_links(wd, target_url=target_url, day_limit=day_limit, sleep_prd=sleep_prd)
    print(f"\n")
    course_status = ["NA"]*len(course_links)

    for i in range(len(course_links)):
        try:
            time.sleep(sleep_prd)
            wd.execute_script(f"window.open('{course_links[i]}')")
            wd.close()
            wd.switch_to.window(wd.window_handles[0])
            print(f"Cleaning Udemy Links: {i+1}/{len(course_links)}",end='\r')
            try:
                button = wd.find_element_by_css_selector('a.course-cta--buy')
                if(button.get_attribute("innerHTML").split('\n')[1] == 'Enroll now'):
                    course_status[i] = "Unenrolled"
                elif(button.get_attribute("innerHTML").split('\n')[1] == 'Go to course'):
                    course_status[i] = "Enrolled"
                elif(button.get_attribute("innerHTML").split('\n')[1] == 'Buy now'):
                    course_status[i] = "Expired"
            except NoSuchElementException:
                try:
                    button = wd.find_element_by_css_selector('a.udlite-heading-md')
                    print(button.get_attribute("innerHTML"))
                    if(button.get_attribute("innerHTML").split('\n')[1] == 'Enroll now'):
                        course_status[i] = "Unenrolled"
                    elif(button.get_attribute("innerHTML").split('\n')[1] == 'Go to course'):
                        course_status[i] = "Enrolled"
                    elif(button.get_attribute("innerHTML").split('\n')[1] == 'Buy now'):
                        course_status[i] = "Expired"
                    else:
                        print("Button text not matched. Here's what I got(split):"+button.get_attribute('innerHTML').split('\n')[1])
                except NoSuchElementException:
                    course_status[i] = "Error"
                    print(f"\nCouldn't find enroll button.")
                except IndexError:
                    if(button.get_attribute("innerHTML") == 'Enroll now'):
                        course_status[i] = "Unenrolled"
                    elif(button.get_attribute("innerHTML") == 'Go to course'):
                        course_status[i] = "Enrolled"
                    elif(button.get_attribute("innerHTML") == 'Buy now'):
                        course_status[i] = "Expired"
                    else:
                        print(f"Button text not matched. Here's what I got: {button.get_attribute('innerHTML')}")
                except Exception as e:
                    course_status[i] = "Error"
                    print(f"\nCouldn't find enroll button.\nError: {e}")
            except Exception as e:
                course_status[i] = "    Error"
                print(f"\nCouldn't find enroll button.\nError: {e}")
                #Get rating
                #try:
        except Exception as e:
            course_status[i] = "Error"
            print(f"\nCouldn't open '{course_links[i]}'.\nError is {e}")
    
    print(f"\nCourse Details: {course_status}")
    print(f"\nCourse Links: {len(course_links)}")
    course_names, course_links, course_status = zip(*((x, y, z) for x, y, z in zip(course_names, course_links, course_status) if "Enrolled" not in z and 'Expired' not in z and 'Error' not in z))
    print(f"\nCourse Details: {course_status}")
    print(f"\nCourse Links: {len(course_links)}")



    return course_names, course_links
