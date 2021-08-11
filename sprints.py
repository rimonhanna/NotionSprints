from notion.client import NotionClient
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
import os

load_dotenv()

# Obtain the `token_v2` value by inspecting your browser cookies on a logged-in (non-guest) session on Notion.so
client = NotionClient(token_v2=os.getenv('NOTION_TOKEN'))

# Access a database using the URL of the database page or the inline block
sprints = client.get_collection_view(os.getenv('SPRINTS_TABLE_URL'))

active_sprints = [x for x in sprints.collection.get_rows() if x.active_sprint]
next_sprints = [x for x in sprints.collection.get_rows() if x.start_date and (x.start_date.start == datetime.today().date() or x.start_date.start == datetime.today().date() + timedelta(-1))]

def is_task_done(task): 
    return task.status in ["Test", "Demo", "Done 🙌"]

def is_task_in_progress(task): 
    return task.status in ["Next Up", "In Progress", "Code Review"]

def is_task_in_backlog(task): 
    return task.status in ["", "In Refinement"]

def end_sprint(active_sprint):
    m_estimate_sum = 0
    s_estimate_sum = 0
    b_estimate_sum = 0

    m_done_sum = 0
    s_done_sum = 0
    b_done_sum = 0

    for task in active_sprint.tasks:
        if not is_task_in_backlog(task):
            if task.m_estimate:
                m_estimate_sum += task.m_estimate

                if is_task_done(task):
                    task.m_done = task.m_estimate
                    m_done_sum += task.m_estimate
                elif task.m_done:
                    m_done_sum += task.m_done

            if task.s_estimate:
                s_estimate_sum += task.s_estimate

                if is_task_done(task):
                    task.s_done = task.s_estimate
                    s_done_sum += task.s_estimate
                elif task.s_done:
                    s_done_sum += task.s_done

            if task.b_estimate:
                b_estimate_sum += task.b_estimate

                if is_task_done(task):
                    task.b_done = task.b_estimate
                    b_done_sum += task.b_estimate
                elif task.b_done:
                    b_done_sum += task.b_done

            if task.status == "Demo":
                task.status = "Done 🙌"

    active_sprint.m_estimate = m_estimate_sum
    active_sprint.m_done = m_done_sum

    active_sprint.s_estimate = s_estimate_sum
    active_sprint.s_done = s_done_sum

    active_sprint.b_estimate = b_estimate_sum
    active_sprint.b_done = b_done_sum

    print(f" {m_estimate_sum=}")
    print(f" {m_done_sum=}")
    print(f" {s_estimate_sum=}")
    print(f" {s_done_sum=}")
    print(f" {b_estimate_sum=}")
    print(f" {b_done_sum=}")

def start_sprint(active_sprint, next_sprint):

    def migrate_unfinished_tasks(active_sprint, next_sprint):
        if active_sprint != next_sprint:
            for task in active_sprint.tasks:
                if is_task_in_progress(task):
                    if task.m_estimate and task.m_done and task.m_done < task.m_estimate:
                        task.m_estimate = task.m_estimate - task.m_done
                        task.m_done = None

                    if task.s_estimate and task.s_done and task.s_done < task.s_estimate:
                        task.s_estimate = task.s_estimate - task.s_done
                        task.s_done = None

                    if task.b_estimate and task.b_done and task.b_done < task.b_estimate:
                        task.b_estimate = task.b_estimate - task.b_done
                        task.b_done = None

                    if task not in next_sprint.tasks:
                        next_sprint.tasks = next_sprint.tasks + [task]

    def calculate_new_sprint_storypoints(next_sprint):
        m_estimate_sum = s_estimate_sum = b_estimate_sum = 0

        for task in next_sprint.tasks:
            if not is_task_in_backlog(task):
                if task.m_estimate:
                    m_estimate_sum += task.m_estimate

                if task.s_estimate:
                    s_estimate_sum += task.s_estimate

                if task.b_estimate:
                    b_estimate_sum += task.b_estimate

        return m_estimate_sum, s_estimate_sum, b_estimate_sum

    migrate_unfinished_tasks(active_sprint, next_sprint)
    m_estimate_sum, s_estimate_sum, b_estimate_sum = calculate_new_sprint_storypoints(next_sprint)

    next_sprint.m_estimate = m_estimate_sum
    next_sprint.s_estimate = s_estimate_sum
    next_sprint.b_estimate = b_estimate_sum

    print(f" {m_estimate_sum=}")
    print(f" {s_estimate_sum=}")
    print(f" {b_estimate_sum=}")

    active_sprint.active_sprint = False
    next_sprint.active_sprint = True

def start_sprint():
    if len(active_sprints) > 0 and len(next_sprints) > 0:
        start_sprint(active_sprints[0], next_sprints[0])
    else:
        print(f"Couldn't find the active sprint {len(active_sprints)} or next sprint {len(next_sprints)}")

def end_sprint():
    if len(active_sprints) > 0:
        end_sprint(active_sprints[0])
    else:
        print(f"Couldn't find an active sprint {len(active_sprints)}")
