from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from Terraform import TerraformResource

terraformResources = []

options = Options()
options.headless = True

driver = webdriver.Firefox(options=options)
driver.get("https://www.terraform.io/docs/providers/aws/")
elements_links = driver.find_elements_by_xpath("//a[contains(@href,'docs/providers/aws/r')]")

for link in elements_links:
    tfResource = TerraformResource(link.get_attribute("href"), link.text, driver)
    terraformResources.append(tfResource)

for resource in terraformResources:
    resource.parse()
    with open('Snippets/' + resource.name + ".sublime-snippet", 'w') as src:
        src.write(resource.get_snippet())
