import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


dr = None

def select_id(driver, id, value):
    shortcut = Select(driver.find_element(By.ID, id))
    shortcut.select_by_value(value)

def select_text(driver, id, text):
    shortcut = Select(driver.find_element(By.ID, id))
    shortcut.select_by_visible_text(text)

def type_id(driver, id, text):
    shortcut = driver.find_element(By.ID, id)
    shortcut.send_keys(text)

def click_id(driver, id):
    shortcut = driver.find_element(By.ID, id)
    shortcut.click()

def clear_id(driver, id):
    shortcut = driver.find_element(By.ID, id)
    shortcut.clear()

def login_for_test_(dr):
    dr.get("http://localhost:5000/")
    click_id(dr, "logging")
    type_id(dr, "login", "test")
    type_id(dr, "password", "test")
    click_id(dr, "submit")

def make_account(dr):
    click_id(dr, "create_account")
    type_id(dr, "login", "test")
    type_id(dr, "password", "test")
    type_id(dr, "email", "test@gmail.com")
    click_id(dr, "submit")

def create_project(dr, name, decription):
    click_id(dr, "add")
    click_id(dr, "add_project")
    type_id(dr, "name", name)
    type_id(dr, "description", decription)
    click_id(dr, "submit")

def create_bug(dr, topic, description, tag):
    click_id(dr, "add")
    click_id(dr, "add_bug")
    type_id(dr, "topic", topic)
    type_id(dr, "description", description)
    type_id(dr, "tag_id", tag)
    click_id(dr, "submit")

@pytest.fixture(scope="function", params = [webdriver.Chrome(),webdriver.Edge(), webdriver.Firefox()])
def fix(request):
    global dr
    dr = request.param
    dr.get("http://localhost:5000/welcome")
    try:
        make_account(dr)
        login_for_test_(dr)
    except:
        pass
    yield dr
    dr.get("http://localhost:5000/test/del/")

@pytest.fixture(scope="class", params = [webdriver.Chrome(),webdriver.Edge(), webdriver.Firefox()])
def search_fix(request):
    global dr
    dr = request.param
    dr.get("http://localhost:5000/welcome")
    try:
        make_account(dr)
        login_for_test_(dr)
    except:
        pass
    create_project(dr, "projekt", "opis")
    create_project(dr, "proje", "descri")
    create_project(dr, "coś innego", "opas")
    create_bug(dr, "błąd", "opis błędu", "")
    create_bug(dr, "z_błąd", "description", "test_tag")
    click_id(dr, "add")
    click_id(dr, "add_bug")
    type_id(dr, "topic", "error")
    type_id(dr, "description", "des")
    type_id(dr, "tag_id", "tag_testowy,test_tag")
    select_text(dr, "project_id", "coś innego")
    select_id(dr, "importance", "błachy")
    click_id(dr, "submit")
    click_id(dr, "home_page")
    click_id(dr, "submit")
    click_id(dr, "bug_topic/1")
    click_id(dr, "change_status")
    yield dr
    dr.get("http://localhost:5000/test/del/")
    dr.quit()

def test_sign(fix):
    # this test checks if the view pages can open without error
    assert dr.find_element(By.ID, "greeting")

def test_add(fix):
    create_project(dr, "test_proj", "test description")
    entry = dr.find_element(By.ID, "project/1")
    assert "test_proj" in entry.text
    entry = dr.find_element(By.ID, "project/description/1")
    assert "test description" in entry.text
    create_bug(dr, "test_bug", "test description", "test_tag")
    entry = dr.find_element(By.ID, "bug_topic/1")
    assert "test_bug" in entry.text
    entry = dr.find_element(By.ID, "bug_tag/1")
    assert "test_tag" in entry.text

def test_edit(fix):
    create_project(dr, "test_proj", "test description")
    click_id(dr, "project/1")
    clear_id(dr, "name")
    type_id(dr, "name", "Edited name")
    clear_id(dr, "description")
    type_id(dr, "description", "Edited description")
    click_id(dr, "submit")
    entry = dr.find_element(By.ID, "project/1")
    assert "Edited name" in entry.text
    entry = dr.find_element(By.ID, "project/description/1")
    assert "Edited description" in entry.text
    create_bug(dr, "test_bug", "test description", "test_tag")
    click_id(dr, "bug_topic/1")
    click_id(dr, "edit")
    clear_id(dr, "topic")
    type_id(dr, "topic", "Edited topic")
    clear_id(dr, "description")
    type_id(dr, "description", "Edited description")
    clear_id(dr, "tag_id")
    type_id(dr, "tag_id", "second_tag")
    click_id(dr, "submit")
    click_id(dr, "home_page")
    entry = dr.find_element(By.ID, "bug_topic/1")
    assert "Edited topic" in entry.text
    entry = dr.find_element(By.ID, "bug_tag/1")
    assert "second_tag" in entry.text

@pytest.mark.usefixtures("search_fix")
class TestSearch:
    def test_user_search(self):
        click_id(dr, "search")
        click_id(dr, "users")
        type_id(dr, "searched", "test")
        click_id(dr, "submit")
        entry = dr.find_element(By.CLASS_NAME, "login")
        assert "test" in entry.text
        clear_id(dr, "searched")
        type_id(dr, "searched", "te")
        click_id(dr, "submit")
        entry = dr.find_element(By.CLASS_NAME, "login")
        assert "test" in entry.text
    def test_project_search(self):
        click_id(dr, "search")
        click_id(dr, "projects")
        type_id(dr, "searched", "pro")
        select_id(dr, "order", "increasing")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "project/1")
        assert "projekt" in entry.text
        entry = dr.find_element(By.ID, "project/2")
        assert "proje" in entry.text
    def test_project_sorting(self):
        select_id(dr, "sor_by", "len_bugs")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "project/1")
        assert "proje" in entry.text
    def test_project_description_search(self):
        click_id(dr, "by_description")
        type_id(dr, "searched", "op")
        select_id(dr, "sor_by", "name")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "project/1")
        assert "coś innego" in entry.text
    def test_bug_search(self):
        click_id(dr, "search")
        click_id(dr, "bugs")
        type_id(dr, "searched", "błąd")
        select_id(dr, "sor_by", "topic")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "z_błąd" in entry.text
    def test_bug_sorting_by_topic(self):
        select_id(dr, "sor_by", "topic")
        select_id(dr, "order", "increasing")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/2")
        assert "z_błąd" in entry.text
    def test_bug_sorting_by_time(self):
        select_id(dr, "sor_by", "id")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "z_błąd" in entry.text
    def test_bug_searching_by_project(self):
        click_id(dr, "by_project")
        type_id(dr, "searched", "coś innego")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
    def test_bug_searching_by_description(self):
        click_id(dr, "by_description")
        type_id(dr, "searched", "des")
        select_id(dr, "sor_by", "importance")
        select_id(dr, "order", "increasing")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "z_błąd" in entry.text
        entry = dr.find_element(By.ID, "bug/2")
        assert "error" in entry.text
    def test_bug_sorting_by_project(self):
        select_id(dr, "sor_by", "project")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/2")
        assert "z_błąd" in entry.text
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
    def test_bug_sorting_by_status(self):
        select_id(dr, "sor_by", "status")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
        entry = dr.find_element(By.ID, "bug/2")
        assert "z_błąd" in entry.text
    def test_bug_searching_by_status(self):
        click_id(dr, "by_status")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/2")
        assert "błąd" in entry.text
        select_id(dr, "stat-status", "resolved")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
    def test_bug_searching_by_importance(self):
        click_id(dr, "by_importance")
        select_id(dr, "search_importance", "Błachy")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
    def test_bug_searching_by_tag(self):
        click_id(dr, "by_tag")
        type_id(dr, "searched", "test_tag")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
        entry = dr.find_element(By.ID, "bug/2")
        assert "z_błąd" in entry.text
        clear_id(dr, "searched")
        type_id(dr, "searched", "tag_testowy")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
        clear_id(dr, "searched")
        type_id(dr, "searched", "test_tag, tag_testowy")
        click_id(dr, "joined")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/1")
        assert "error" in entry.text
        type_id(dr, "searched", "test_tag, tag_testowy")
        click_id(dr, "submit")
        entry = dr.find_element(By.ID, "bug/2")
        assert "z_błąd" in entry.text