import os
import time
import shutil
import selenium
import selenium.webdriver.support.ui
import selenium.webdriver.chrome.options
import selenium.webdriver.common.action_chains

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import InvalidArgumentException
from selenium.webdriver.support import expected_conditions as EC


DOWNLOAD_DIRECTORY = "download"


class Session:
    def __init__(self, act_doc_viewer=False):
        options = selenium.webdriver.chrome.options.Options()

        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--kiosk-printing")
        # options.add_argument("--no-sand-box")  # in testing phase
        # options.add_argument("--headless")  # in testing phase

        options.add_experimental_option("detach", True)
        prefs = {"download.default_directory": DOWNLOAD_DIRECTORY,
                 "savefile.default_directory": DOWNLOAD_DIRECTORY,
                 "download.prompt_for_download": False,
                 "plugins.always_open_pdf_externally": (not act_doc_viewer),
                 "safebrowsing_enabled": False  # in testing phase
                 }
        options.add_experimental_option("prefs", prefs)

        self.driver = selenium.webdriver.Chrome(options=options)

        self.driver.set_window_position(0, 0)
        self.driver.maximize_window()

        self.actions = selenium.webdriver.common.action_chains.ActionChains(self.driver)
        self.wait = selenium.webdriver.support.ui.WebDriverWait(self.driver, 60)


    def login_mail(self, email_user, email_pass):
        self.driver.get("https://sesp.pr.gov.br/")
        self.driver.implicitly_wait(5)
        self.driver.find_element(By.ID, "user").send_keys(email_user)
        self.actions.send_keys(Keys.TAB).perform()
        self.actions.send_keys(email_pass).send_keys(Keys.TAB).send_keys(Keys.RETURN).perform()
        self.wait.until(EC.url_matches("https://sesp.pr.gov.br/expressoMail1_2/index.php"))


    def prepare_email(self, subject, text, recipient, conf_reading=False):
        btn_new = "//tr[2]/td[@class='content-menu-td']/div[@class='em_div_sidebox_menu']/" \
                  "span[@class='em_sidebox_menu']"

        self.driver.find_element(By.XPATH, btn_new).click()

        self.driver.find_element(By.ID, "return_receipt_1").click() if conf_reading else None

        self.driver.find_element(By.ID, "to_1").send_keys(recipient)
        self.driver.find_element(By.ID, "subject_1").send_keys(subject)
        self.actions.send_keys(Keys.TAB).send_keys(text).perform()


    def attach_annex(self, file_name, annexes_path, new_annex_name=None):
        file_name =file_name if file_name.endswith(".pdf") else f"{file_name}.pdf"
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path_annex = os.path.join(script_dir, annexes_path, file_name)

        if not os.path.exists(path_annex):
            return 1

        if new_annex_name:
            file_ext = os.path.splitext(path_annex)[1]
            
            temp_dir = os.path.join(script_dir, "Annexes_Temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"{new_annex_name}{file_ext}")

            try:
                shutil.copy2(path_annex, temp_path)
            except OSError:
                return 1
            
            attach_path = temp_path
        else:
            attach_path = path_annex

        link_annex = "//tr[10]/td[2]/a"
        try:
            self.driver.find_element(By.XPATH, link_annex).click()
            self.driver.find_element(By.ID, "inputFile_1_1").send_keys(attach_path)
        except InvalidArgumentException:
            return 1
        
        return 0


    def send(self):
        try:
            self.driver.find_element(By.ID, "send_button_1").click()
            self.wait.until(EC.invisibility_of_element_located((By.ID, "send_button_1")))
            return 0
        except TimeoutException:
            return 1
        

    def reset(self):
        self.driver.refresh()
        try:
            self.wait.until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert.accept()
            self.wait.until(EC.invisibility_of_element_located((By.ID, "send_button_1")))
        except NoAlertPresentException:
            pass


    def print_page(self):
        self.driver.execute_script("window.print()")


    def save_receipt(self, subject):
        self.driver.find_element(By.ID, "lINBOX/Enviadostree_folders").click()
        time.sleep(2)
        self.driver.find_element(By.XPATH, f"//*[contains(text(), '{subject}')]").click()
        time.sleep(2)
        self.driver.find_element(By.XPATH, "//*[contains(text(), 'Mostrar detalhes')]").click()
        time.sleep(2)

        # before_files = os.listdir(_utils.paths.source)
        self.print_page()
        # file = _utils.control_download(before_files)
        # file = _utils.check_download()
        # os.rename(f"{_utils.paths.source}/{file}", f"{_utils.paths.source}/{new_file_name}.pdf")
        # os.rename(file, f"{_utils.paths.source}/{new_file_name}.pdf")


    def end_session(self):
        self.driver.quit()
