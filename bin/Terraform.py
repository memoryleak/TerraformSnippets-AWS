from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.by import By

class TerraformResourceArgument:
    def __init__(self, name, description, optional):
        self.name = name
        self.description = description
        self.optional = optional

    def get_snippet(self, index):
        return self.name + " = \"${" + str((index + 1)) + ":" + (
            "Optional" if self.optional is True else "Required"
        ) + "}\"\n"


class TerraformResourceAttribute:
    def __init__(self, name, description, optional):
        self.name = name
        self.description = description
        self.optional = optional

    def get_snippet(self, index):
        return self.name + " = \"${" + str((index + 1)) + ":" + (
            "Optional" if self.optional is True else "Required"
        ) + "}\"\n"


class TerraformResource:
    driver: WebDriver

    def __init__(self, url, name, driver):
        self.url = url
        self.name = name
        self.driver = driver
        self.arguments = []

    def parse(self):
        self.driver.get(self.url)
        ul_element = self.driver.find_element(By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/article/div[2]/div/div/ul[1]")
        lines = ul_element.text.split("\n")

        print("Arguments >>> {}".format(lines))

        for line in lines:
            line_option = line.split('-')
            if len(line_option) == 2:
                name = line_option[0].strip()
                description = line_option[1].strip()
                optional = (description.find("Optional") != -1)
                self.arguments.append(TerraformResourceArgument(name, description, optional))
        pass

    def get_snippet(self):
        index = 2
        snippets = "<snippet>\n<content><![CDATA[\n"
        snippets += "resource \"" + self.name + "\" \"" + self.name + "_${1:suffix}\" {\n"

        for argument in self.arguments:
            snippets += "\t" + argument.get_snippet(index)
            index += 1

        snippets += "}\n]]></content>\n<tabTrigger>" + self.name + "</tabTrigger>\n<scope>source.terraform</scope>\n" \
                                                                   "</snippet>\n"
        return snippets
