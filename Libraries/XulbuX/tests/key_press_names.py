import keyboard

while True:
    event = keyboard.read_event()
    if event.event_type == 'down':
        print(f'Key pressed: {event.name}')
