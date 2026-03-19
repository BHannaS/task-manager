import streamlit as st
import uuid
import json
import os
import re
from datetime import date

FILE_NAME = "tasks.json"


def load_tasks():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            tasks = json.load(file)

        for task in tasks:
            if "priority" not in task:
                task["priority"] = "Medium"
            if "deadline" not in task:
                task["deadline"] = date.today().isoformat()

        return tasks
    return []


def save_tasks(tasks):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(tasks, file, ensure_ascii=False, indent=4)


def is_valid_task_text(text):
    pattern = r"^[A-Za-zÄÖÜäöüß0-9\s\.,!\?\-\'\(\)]+$"
    return bool(re.fullmatch(pattern, text))


def priority_value(priority):
    mapping = {
        "High": 3,
        "Medium": 2,
        "Low": 1
    }
    return mapping.get(priority, 0)


def priority_badge(priority):
    if priority == "High":
        return '<span class="badge badge-high">High</span>'
    elif priority == "Medium":
        return '<span class="badge badge-medium">Medium</span>'
    return '<span class="badge badge-low">Low</span>'


st.markdown("""
<style>
.main-title {
    font-size: 2.1rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}
.subtitle {
    color: #6b7280;
    margin-bottom: 1rem;
}
.task-card {
    padding: 0.6rem 0.8rem;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
    margin-bottom: 0.5rem;
    background-color: #ffffff;
}
.done-task {
    opacity: 0.55;
    text-decoration: line-through;        
}
.badge {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-left: 0.5rem;
}
.badge-high {
    background-color: #fee2e2;
    color: #b91c1c;
}
.badge-medium {
    background-color: #fef3c7;
    color: #b45309;
}
.badge-low {
    background-color: #dcfce7;
    color: #15803d;
}
.deadline-text {
    font-size: 0.85rem;
    color: #6b7280;
}
.section-space {
    margin-top: 0.8rem;
    margin-bottom: 0.2rem;
}
</style>
""", unsafe_allow_html=True)


st.markdown('<div class="main-title">Task Manager</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Tasks, priorities, deadlines.</div>',
    unsafe_allow_html=True
)

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

if "editing_task_id" not in st.session_state:
    st.session_state.editing_task_id = None


# ---------- Add task ----------
with st.form("task_form", clear_on_submit=True):
    form_col1, form_col2, form_col3 = st.columns([4, 2, 2])

    with form_col1:
        task = st.text_input("Task")

    with form_col2:
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])

    with form_col3:
        deadline = st.date_input("Deadline", value=date.today())

    submitted = st.form_submit_button("Add")

    if submitted:
        task = task.strip()

        if not task:
            st.warning("Please enter a task.")
        elif not is_valid_task_text(task):
            st.error("Use only English/German letters, numbers, spaces, and basic punctuation.")
        else:
            st.session_state.tasks.append({
                "id": str(uuid.uuid4()),
                "title": task,
                "done": False,
                "priority": priority,
                "deadline": deadline.isoformat()
            })
            save_tasks(st.session_state.tasks)


# ---------- Overview ----------
total_tasks = len(st.session_state.tasks)
done_tasks = sum(1 for task in st.session_state.tasks if task["done"])
active_tasks = total_tasks - done_tasks

st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)

top_left, top_right = st.columns([3, 2])

with top_left:
    st.subheader("Overview")
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric("Total", total_tasks)

    with metric_col2:
        st.metric("Active", active_tasks)

    with metric_col3:
        st.metric("Done", done_tasks)

with top_right:
    st.subheader("Filter")
    filter_option = st.radio(
        "Filter",
        ["All", "Active", "Done"],
        horizontal=True,
        label_visibility="collapsed"
    )

    if st.button("Clear completed"):
        st.session_state.tasks = [
            task for task in st.session_state.tasks
            if not task["done"]
        ]
        save_tasks(st.session_state.tasks)
        st.rerun()


# ---------- Search and Sort ----------
st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
st.subheader("Search and Sort")

search_query = st.text_input("Search").strip()

sort_option = st.radio(
    "Sort",
    [
        "Newest first",
        "A-Z",
        "Deadline ascending",
        "Deadline descending",
        "Priority high first",
        "Priority low first"
    ],
    horizontal=True
)


# ---------- Filter tasks ----------
if filter_option == "All":
    filtered_tasks = st.session_state.tasks.copy()
elif filter_option == "Active":
    filtered_tasks = [task for task in st.session_state.tasks if not task["done"]]
else:
    filtered_tasks = [task for task in st.session_state.tasks if task["done"]]

if search_query:
    filtered_tasks = [
        task for task in filtered_tasks
        if search_query.lower() in task["title"].lower()
    ]

if sort_option == "A-Z":
    filtered_tasks.sort(key=lambda task: task["title"].lower())
elif sort_option == "Deadline ascending":
    filtered_tasks.sort(key=lambda task: task["deadline"])
elif sort_option == "Deadline descending":
    filtered_tasks.sort(key=lambda task: task["deadline"], reverse=True)
elif sort_option == "Priority high first":
    filtered_tasks.sort(key=lambda task: priority_value(task["priority"]), reverse=True)
elif sort_option == "Priority low first":
    filtered_tasks.sort(key=lambda task: priority_value(task["priority"]))


# ---------- Tasks ----------
st.markdown('<div class="section-space"></div>', unsafe_allow_html=True)
st.subheader("Tasks")

task_to_delete = None
changed = False

for task in filtered_tasks:
    if st.session_state.editing_task_id == task["id"]:
        st.markdown(f"**Editing:** {task['title']}")

        edit_title = st.text_input(
            "Task",
            value=task["title"],
            key=f"edit_title_{task['id']}"
        )

        priority_options = ["Low", "Medium", "High"]
        current_priority_index = priority_options.index(task["priority"])

        edit_priority = st.selectbox(
            "Priority",
            priority_options,
            index=current_priority_index,
            key=f"edit_priority_{task['id']}"
        )

        edit_deadline = st.date_input(
            "Deadline",
            value=date.fromisoformat(task["deadline"]),
            key=f"edit_deadline_{task['id']}"
        )

        col_save, col_cancel = st.columns(2)

        with col_save:
            if st.button("Save", key=f"save_{task['id']}"):
                edit_title = edit_title.strip()

                if not edit_title:
                    st.warning("Task cannot be empty.")
                elif not is_valid_task_text(edit_title):
                    st.error("Use only English/German letters, numbers, spaces, and basic punctuation.")
                else:
                    task["title"] = edit_title
                    task["priority"] = edit_priority
                    task["deadline"] = edit_deadline.isoformat()
                    st.session_state.editing_task_id = None
                    save_tasks(st.session_state.tasks)
                    st.rerun()

        with col_cancel:
            if st.button("Cancel", key=f"cancel_{task['id']}"):
                st.session_state.editing_task_id = None
                st.rerun()

    else:
        row_col1, row_col2, row_col3 = st.columns([6, 1, 1])

        with row_col1:
            done_col, info_col = st.columns([1, 12])

            with done_col:
                new_done = st.checkbox(
                    "",
                    value=task["done"],
                    key=f"done_{task['id']}"
                )

            with info_col:
                title_style = "done-task" if task["done"] else ""

                st.markdown(
                    f"""
                    <div class="{title_style}" style="font-size: 1.08rem; font-weight: 600; margin-bottom: 0.15rem;">
                        {task['title']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"""
                    {priority_badge(task['priority'])}
                    <span class="deadline-text" style="margin-left: 8px;">Deadline: {task['deadline']}</span>
                    """,
                    unsafe_allow_html=True
                )

            if new_done != task["done"]:
                task["done"] = new_done
                changed = True

        with row_col2:
            st.write("")
            if st.button("Edit", key=f"edit_{task['id']}"):
                st.session_state.editing_task_id = task["id"]
                st.rerun()

        with row_col3:
            st.write("")
            if st.button("Delete", key=f"delete_{task['id']}"):
                task_to_delete = task["id"]

        st.divider()


if task_to_delete is not None:
    st.session_state.tasks = [
        task for task in st.session_state.tasks
        if task["id"] != task_to_delete
    ]
    if st.session_state.editing_task_id == task_to_delete:
        st.session_state.editing_task_id = None
    save_tasks(st.session_state.tasks)
    st.rerun()

if changed:
    save_tasks(st.session_state.tasks)
    st.rerun()