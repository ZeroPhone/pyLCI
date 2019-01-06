import os
import pickle

from helpers import ZP_DATA_DIR, Singleton, flatten, setup_logger
from vcard_converter import VCardContactConverter
from contact import Contact

logger = setup_logger(__name__, "warning")

SAVE_FILENAME = "contacts.pickle"

class AddressBook(Singleton):
    def __init__(self):
        """ This class provides the address book used by the Contacts
        application.

        Adds a single contact
        >>> a = AddressBook()
        >>> c1 = Contact(name="john", org="wikipedia")
        >>> a.add_contact(c1)
        >>> len(a.contacts)
        1

        Adds another contact so similar it will be merged with the previous
        >>> c2 = Contact()
        >>> c2.name = ["john"]
        >>> c2.telephone = ["911"]
        >>> a.add_contact(c2)

        the updated contact is retrieved
        >>> a.find(name="john").telephone
        ['911']
        >>> a.find(name="john").org
        ['wikipedia']
        >>> len(a.contacts)
        1

        Add a third similar contact, without auto_merge
        >>> c3 = Contact(name="John", telephone="911")
        >>> a.add_contact(c3, auto_merge=False)
        >>> len(a.contacts)
        2
        """
        self._contacts = []
        self._load_from_file()

    @staticmethod
    def _get_save_file_path():
        return os.path.join(ZP_DATA_DIR, SAVE_FILENAME)

    def _load_from_file(self):
        save_path = self._get_save_file_path()
        if not os.path.exists(save_path):
            logger.error("Could not load. File {} not found".format(save_path))
            return
        with open(self._get_save_file_path(), 'r') as f_save:
            self._contacts = pickle.load(f_save)

    def _save_to_file(self):
        for c in self.contacts:
            c.consolidate()
        with open(self._get_save_file_path(), 'w') as f_save:
            pickle.dump(self._contacts, f_save)

    def _get_contacts_with(self, attribute_name):
        # type: (str) -> list
        return [c for c in self.contacts if len(getattr(c, attribute_name))]

    def _find_best_duplicate(self, contact):
        # type: (Contact) -> Contact
        match_score_contact_list = self._find_duplicates(contact)
        if match_score_contact_list[0][0] > 0:
            return match_score_contact_list[0][1]

    def _find_duplicates(self, contact):
        # type: (Contact) -> list
        if contact in self._contacts:
            return [1, contact]
        match_score_contact_list = [(c.match_score(contact), c) for c in
                                    self.contacts]

        def cmp(a1, a2):
            # type: (tuple, tuple) -> int
            return a1[0] > a2[0]

        return sorted(match_score_contact_list, cmp=cmp)

    @property
    def contacts(self):
        """ Returns a list containing all the contacts of this address book."""
        # type: () -> list
        return self._contacts

    def add_contact(self, contact, auto_merge=True):
        """Add a contact to this address book.

        Args:

            * ``contact``: the contact object to add

        Kwargs:

            * ``auto_merge``: wether to automatically merge ``contact`` if
            there already is a similar entry in the address book
        """
        # type: (Contact, bool) -> None
        if not auto_merge or not len(self.contacts):
            self._contacts.append(contact)
            return

        duplicate = self._find_best_duplicate(contact)
        if duplicate:
            duplicate.merge(contact)
        else:
            self._contacts.append(contact)

        # Save changes to disk
        self._save_to_file()

    def reset(self):
        """Delete all the contacts of this address book."""
        self._contacts = []
        self._save_to_file()

    def find(self, **kwargs):
        """Search for a contact in this address book and return the best
        match.
        """
        # type: (dict) -> Contact
        # simple wrapper around find_best_duplicate
        c = Contact(**kwargs)
        return self._find_best_duplicate(c)

    def import_vcards_from_directory(self, directory):
        """Import every VCF file in ``directory`` to this address book.

        Args:

            * ``directory``: absolute path to a directory containing VCF files
        """
        logger.info("Import vCards from {}".format(directory))

        # Extract *cvf files from the directory
        home = os.path.expanduser(directory)
        if not os.path.exists(home):
            os.mkdir(home)
        vcard_files = [os.path.join(home, f) for f in os.listdir(home) if
                       f.lower().endswith("vcf")]

        # Import into current AddressBook instance
        parsed_contacts = VCardContactConverter.from_vcards(vcard_files)
        for new in parsed_contacts:
            is_duplicate = new in self._contacts

            if is_duplicate:
                logger.info("Ignore duplicated contact for: {}"
                            .format(new.name))
                break

            self.add_contact(new)
