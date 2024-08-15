import pytest
import context

def test_validation_switched_off():
  # AirPlay names can only be 50chars long; test that this obj can be created without validation
  # enabled, and that it does do validation normally
  kwargs = {
    'name': 'a'*51,
    'mock': True,
    'ap2': False,
  }
  assert context.amplipi.streams.AirPlay(validate=False, **kwargs)

  with pytest.raises(context.amplipi.streams.base_streams.InvalidStreamField):
    context.amplipi.streams.AirPlay(**kwargs)


