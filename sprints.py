from notion.client import NotionClient
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
import os

load_dotenv()

# Obtain the `token_v2` value by inspecting your browser cookies on a logged-in (non-guest) session on Notion.so
token = os.getenv('NOTION_TOKEN')
client = NotionClient(token_v2=token)

# Access a database using the URL of the database page or the inline block
sprints = client.get_collection_view(os.getenv('SPRINTS_TABLE_URL'))
current_date = datetime.today().date()

def compare_date(date1, date2, difference):
    return timedelta(-1) <= date1 - date2 <= timedelta(difference)

current_sprints = [row for row in sprints.collection.get_rows() 
                  if row.start_date 
                  and row.end_date 
                  and compare_date(current_date, row.start_date.start, 17) 
                  and compare_date(current_date, row.end_date.start, 3)]

next_sprints = [row for row in sprints.collection.get_rows() 
                if row.start_date 
                and row.end_date 
                and compare_date(current_date, row.start_date.start, 3) 
                and compare_date(row.end_date.start, current_date, 15)]

print(current_sprints)
print(next_sprints)

def is_task_done(task): 
    return task.status in ["Demo", "Done 🙌"]

def is_task_in_progress(task): 
    return task.status in ["Next Up", "In Progress", "Code Review"]

def is_task_in_backlog(task): 
    return task.status in ["", "Refinement"]

def new_sprint_points(estimate, done):
    if estimate and done and estimate > done:
        return estimate - done, None
    else:
        return estimate, done

def end_old_sprint(current_sprint):
    m_done_sum = s_done_sum = b_done_sum = m_actual_sum = s_actual_sum = b_actual_sum = 0

    def calculate_sum(task, actual_sum, done_sum, estimate, done):
        if estimate:
            actual_sum += estimate
            if not is_task_in_progress(task):
                done = estimate
                done_sum += estimate
            elif done:
                done_sum += done
        return actual_sum, done_sum, done


    for task in current_sprint.tasks:
        if task.alive and not is_task_in_backlog(task):
            m_actual_sum, m_done_sum, task.m_done = calculate_sum(task, m_actual_sum, m_done_sum, task.m_estimate, task.m_done)
            s_actual_sum, s_done_sum, task.s_done = calculate_sum(task, s_actual_sum, s_done_sum, task.s_estimate, task.s_done)
            b_actual_sum, b_done_sum, task.b_done = calculate_sum(task, b_actual_sum, b_done_sum, task.b_estimate, task.b_done)

            if task.status == "Demo":
                task.status = "Done 🙌"

    current_sprint.m_done = m_done_sum
    current_sprint.s_done = s_done_sum
    current_sprint.b_done = b_done_sum

    current_sprint.m_actual = m_actual_sum
    current_sprint.s_actual = s_actual_sum
    current_sprint.b_actual = b_actual_sum

    print(f" {m_actual_sum=}")
    print(f" {s_actual_sum=}")
    print(f" {b_actual_sum=}")

    print(f" {m_done_sum=}")
    print(f" {s_done_sum=}")
    print(f" {b_done_sum=}")

def start_new_sprint(current_sprint, next_sprint):

    def migrate_unfinished_tasks(current_sprint, next_sprint):
        if current_sprint != next_sprint:
            for task in current_sprint.tasks:
                if task.alive and not is_task_done(task):
                    task.m_estimate, task.m_done = new_sprint_points(task.m_estimate, task.m_done)
                    task.s_estimate, task.s_done = new_sprint_points(task.s_estimate, task.s_done)
                    task.b_estimate, task.b_done = new_sprint_points(task.b_estimate, task.b_done)

                    if task not in next_sprint.tasks:
                        next_sprint.tasks = next_sprint.tasks + [task]

    def calculate_new_sprint_storypoints(next_sprint):
        m_estimate_sum = s_estimate_sum = b_estimate_sum = 0

        for task in next_sprint.tasks:
            if task.alive and is_task_in_progress(task):
                if is_task_in_backlog(task):
                    task.status = "Next Up"

                if task.m_estimate and not task.m_done:
                    m_estimate_sum += task.m_estimate

                if task.s_estimate and not task.s_done:
                    s_estimate_sum += task.s_estimate

                if task.b_estimate and not task.b_done:
                    b_estimate_sum += task.b_estimate

        return m_estimate_sum, s_estimate_sum, b_estimate_sum

    migrate_unfinished_tasks(current_sprint, next_sprint)
    m_estimate_sum, s_estimate_sum, b_estimate_sum = calculate_new_sprint_storypoints(next_sprint)

    next_sprint.m_estimate = m_estimate_sum
    next_sprint.s_estimate = s_estimate_sum
    next_sprint.b_estimate = b_estimate_sum

    print(f" {m_estimate_sum=}")
    print(f" {s_estimate_sum=}")
    print(f" {b_estimate_sum=}")

    current_sprint.active_sprint = False
    next_sprint.active_sprint = True

def start_sprint():
    if len(current_sprints) > 0 and len(next_sprints) > 0:
        start_new_sprint(current_sprints[0], next_sprints[len(next_sprints) - 1])
    else:
        print(f"Couldn't find the current sprint {len(current_sprints)} or next sprint {len(next_sprints)}")

def end_sprint():
    if len(current_sprints) > 0:
        end_old_sprint(current_sprints[0])
    else:
        print(f"Couldn't find an current sprint {len(current_sprints)}")
