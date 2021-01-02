"""Base class for all PDF model classes."""
import logging

LOG = logging.getLogger(__name__)


class ModelBase:
    """Base class for all documentation models."""

    def to_dict(self):
        """
        Turn all object attributes into a dictionary.

        The method steps into sub-objects if they are also a ModelBase instance.
        """
        vars_dict = vars(self).copy()
        delete_backref_keys = []
        for key, value in vars_dict.items():
            if key.startswith('b_'):
                delete_backref_keys.append(key)
            else:
                if isinstance(value, ModelBase):
                    vars_dict[key] = value.to_dict()
        # delete back references
        for key in delete_backref_keys:
            del vars_dict[key]

        return vars_dict

    def check(self):
        """Check if members are not set."""
        for key, value in vars(self).items():
            if value is None:
                LOG.warning('The member %s of class %s is None', key, type(self).__name__)

    def __repr__(self):
        """Overwrite the object representation for better debugging."""
        if hasattr(self, 'id_'):
            return '{0}({1!r})'.format(self.__class__.__name__, self.id_)  # pylint: disable=no-member
        return '{0}()'.format(self.__class__.__name__)
