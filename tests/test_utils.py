import context

def test_get_folder():
  print(context.amplipi.utils.get_folder("streams", mock=True))
  assert context.amplipi.utils.get_folder("streams", mock=True).endswith("/amplipi-dev/streams")
  assert context.amplipi.utils.get_folder("web", mock=True).endswith("/.config/amplipi/web")
  assert context.amplipi.utils.get_folder("config", mock=True).endswith("/.config/amplipi")
