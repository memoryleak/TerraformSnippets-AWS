from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

from Terraform import TerraformResource

terraformResources = []

options = Options()
options.headless = True

driver = webdriver.Firefox(options=options)
driver.get("https://registry.terraform.io/providers/hashicorp/aws/latest/docs")

driver.implicitly_wait(10)

dropdown = driver.find_elements(By.CLASS_NAME, 'menu-list-category-link')
for opt in dropdown:
    opt.click()

elements_links = driver.find_elements(By.XPATH, "//*[contains(@href,'providers/hashicorp/aws/latest/docs/r')]")

print("Creating Element Links...")
for link in elements_links:
    tfResource = TerraformResource(link.get_attribute("href"), link.text, driver)
    terraformResources.append(tfResource)

for resource in terraformResources:
    resource.parse()
    with open('../Snippets/' + resource.name + ".sublime-snippet", 'w') as src:
        src.write(resource.get_snippet())
    print(">>>" + resource.name + "\n")

driver.close()
