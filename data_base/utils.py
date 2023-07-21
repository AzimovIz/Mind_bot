from typing import List

from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import sessionmaker

from data_base.models import Marker, Note

engine = create_engine('sqlite:///data.db')

Session = sessionmaker(bind=engine)
session = Session()


def create_marker(user_id, name, parent_marker=None):
    user_id = str(user_id)
    if parent_marker and not session.scalars(
            select(Marker).where(Marker.id == int(parent_marker))).first().user_id == user_id:
        return False

    marker = Marker(user_id=user_id, value=name, parent=int(parent_marker) if parent_marker else None)
    session.add(marker)
    session.commit()
    return marker


def delete_marker(user_id, marker_id):
    user_id = str(user_id)
    if (maker := session.scalars(select(Marker).where(Marker.id == int(marker_id))).first()).user_id == user_id:
        maker.delete()
        return True
    return False


def create_note(user_id, marker, value):
    user_id = str(user_id)
    if not session.scalars(select(Marker).where(Marker.id == int(marker))).first().user_id == user_id:
        return False

    note = Note(value=value, marker=int(marker))
    session.add(note)
    session.commit()
    return note


def delete_note(user_id, note_id):
    user_id = str(user_id)
    note = session.scalars(select(Note).where(Note.id == int(note_id))).first()
    if note.get_marker().user_id == user_id:
        note.delete()
        return True
    return False


def delete_note_pos(user_id, marker_id, note_pos):
    notes = get_notes(user_id, marker_id)
    note_id = notes[int(note_pos)]["id"]
    delete_note(user_id, note_id)

def get_root_markers(user_id) -> List[Marker]:
    markers = session.scalars(select(Marker).filter(and_(Marker.user_id == str(user_id)), Marker.parent == None))
    # markers = [i.to_dict() for i in markers]
    return markers


def get_child_markers(user_id, marker):
    markers = session.scalars(select(Marker).where(Marker.user_id == str(user_id)).filter(Marker.parent == int(marker)))
    # markers = [i.to_dict() for i in markers]
    return markers


def get_path(user_id, marker):
    marker = session.scalars(select(Marker).filter(and_(Marker.user_id == str(user_id),
                                                        Marker.id == int(marker)))).first()
    if marker.parent:
        return get_path(user_id, marker.parent) + [marker.value, ]
    else:
        return [marker.value, ]


def get_parent_marker(user_id, marker):
    marker = session.scalars(select(Marker).filter(and_(Marker.user_id == str(user_id),
                                                        Marker.id == int(marker)))).first()
    return marker.parent


def get_notes_from_location(user_id, location):
    name = [i for i in location.split("/") if i]
    marker = session.scalars(select(Marker).where(and_(Marker.value == name[-1], Marker.user_id == user_id))).first()
    return read_notes(user_id, marker.id)


def get_notes(user_id, marker):
    marker = session.scalars(
        select(Marker).filter(Marker.user_id == str(user_id)).filter(Marker.id == int(marker))
    ).first()
    if not marker:
        return [{"value": "Пусто"}, ]
    notes = [i.to_dict() for i in marker.get_notes()]
    return notes


def read_notes(user_id, marker):
    notes = get_notes(user_id, marker)
    return "\n".join([i["value"] for i in notes])


def get_tree(user_id):
    return "".join([i.tree() for i in get_root_markers(user_id)])


if __name__ == '__main__':
    print(get_tree("12"))