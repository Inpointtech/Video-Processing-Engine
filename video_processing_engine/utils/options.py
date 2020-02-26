"""Utility for interacting with cmd using questionary."""

import os
from typing import List, Optional, Union

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from questionary import Choice, select, text


def confirm(question: str) -> bool:
  """Provide Yes or No options.
  Asks for confirmation. Provides Yes or No options to confirm.

  Args:
    question: Question for yes-no options.

  Notes:
    It is recommended to use this function by assigning it to a
    variable & then the variable should be used in an if-else condition
    to invoke the action.
  """
  return select(question, [Choice('Yes', True), Choice('No', False)]).ask()


def choose(question: str, choice_dict: dict) -> str:
  """Provides options.

  Provides options to choose from. These options are then to be used
  for further code execution.

  Args:
    question: Question or Message presenting multiple options.
    choice_dict: Dictionary to choose from.

  Notes:
    It is recommended to use this function when any one of the
    multiple options needs to be selected.
  """
  return select(question, [Choice(v, k) for k, v in choice_dict.items()]).ask()


def select_file(question: str, dir_name: str) -> str:
  """Provides list of files.

  Provides option to select the file from a directory.

  Args:
    question: Question or Message selecting multiple files.
    dir_name: Directory from which the file needs to be chosen from.
  """
  # You can find the reference code here:
  # https://stackoverflow.com/questions/1747817/create-a-dictionary-
  # with-list-comprehension
  files = {index[0]: index[1] for index in enumerate(os.listdir(dir_name))}
  key = select(question, [Choice(v, k) for k, v in files.items()]).ask()
  return os.path.join(dir_name, files.get(key, 'new_file.xa'))


def answer(question: str) -> Optional[str]:
  """Takes input for question.

  Answers the asked question.

  Args:
    question: Question that needs to be asked for expecting answer.

  Notes:
    It is recommended to use this function while taking inputs.
  """
  # Asks question until it is responded with something.
  question = ''.join([question, '»'])
  while True:
    revert = text(question).ask()
    if revert == '':
      option = confirm('No inputs received. Would you like to try that again?')
      # Asks the same question again if a blank response is given.
      while option is False:
        return None if option else revert
    else:
      return revert


def ask_numbers(question: str) -> float:
  """Takes input for numeric questions.

  Answers the asked question by numbers.

  Args:
    question: Question that needs to be asked for expecting answer.

  Notes:
    It is recommended to use this function while taking inputs.
  """
  # Asks question until it is responded with something.
  question = ''.join([question, '»'])
  while True:
    revert = float(text(question).ask())
    if revert == '' or revert < 0:
      option = confirm(
        'No valid input received. Would you like to try that again?')
      # Asks the same question again if a no response is given.
      while option is False:
        return 0.0 if option else float(revert)
    else:
      return float(revert)
