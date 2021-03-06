# -*- coding: utf-8 -*-
r"""
Sage Explorer in Jupyter Notebook

EXAMPLES ::
from sage.combinat.tableau import StandardTableaux
from SageExplorer import *
t = StandardTableaux(15).random_element()
widget = SageExplorer(t)
display(t)

AUTHORS:
- Odile Bénassy, Nicolas Thiéry

"""
import yaml, os, re, six, operator as OP
from inspect import getargspec, getmembers, getmro, isclass, isfunction, ismethod, ismethoddescriptor, isabstract
from functools import lru_cache
try: # Are we in a Sage environment?
    import sage.all
    from sage.misc.sageinspect import sage_getargspec as getargspec
    #from sage.misc.sphinxify import sphinxify
except:
    pass

EXCLUDED_MEMBERS = ['__init__', '__repr__', '__str__']
OPERATORS = {'==' : OP.eq, '<' : OP.lt, '<=' : OP.le, '>' : OP.gt, '>=' : OP.ge}
CONFIG_PROPERTIES = yaml.load(open(os.path.join(os.path.dirname(__file__),'properties.yml')), yaml.SafeLoader)

import __main__
def eval_in_main(s):
    """
    Evaluate the expression `s` in the global scope

    TESTS::
        sage: from new_sage_explorer.explored_member import eval_in_main
        sage: from sage.combinat.tableau import Tableaux
        sage: eval_in_main("Tableaux")
        <class 'sage.combinat.tableau.Tableaux'>
    """
    try:
        return eval(s, sage.all.__dict__)
    except:
        return eval(s, __main__.__dict__)


class ExploredMember(object):
    r"""
    A member of an explored object: method, attribute ..
    """
    vocabulary = ['name', 'member', 'parent', 'member_type', 'doc', 'origin', 'overrides', 'privacy', 'prop_label', 'args', 'defaults']

    def __init__(self, name, **kws):
        r"""
        A method or attribute.
        Must have a name.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.name
            'conjugate'
        """
        self.name = name
        for arg in kws:
            try:
                assert arg in self.vocabulary
            except:
                raise ValueError("Argument '%s' not in vocabulary." % arg)
            setattr(self, arg, kws[arg])

    def compute_member(self, parent=None):
        r"""
        Get method or attribute value, given the name.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.compute_member()
            sage: m.member
            <bound method Partitions_all_with_category.element_class.conjugate of [3, 3, 2, 1]>
        """
        if hasattr(self, 'member') and not parent:
            return
        if not parent and hasattr(self, 'parent'):
            parent = self.parent
        if not parent:
            return
        self.parent = parent
        self.member = getattr(parent, self.name)
        self.doc = self.member.__doc__

    def compute_doc(self, parent=None):
        r"""
        Get method or attribute documentation, given the name.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.compute_doc()
            sage: m.doc[:100]
            '\n        Return the conjugate partition of the partition ``self``. This\n        is also called the a'
        """
        if hasattr(self, 'member'):
            self.doc = self.member.__doc__
        else:
            self.compute_member(parent)

    def compute_member_type(self, parent=None):
        r"""
        Get method or attribute value, given the name.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('conjugate', parent=p)
            sage: m.compute_member_type()
            sage: assert 'method' in m.member_type
        """
        if not hasattr(self, 'member'):
            self.compute_member(parent)
        if not hasattr(self, 'member'):
            raise ValueError("Cannot determine the type of a non existent member.")
        m = re.match("<(type|class) '([.\\w]+)'>", str(type(self.member)))
        if m and ('method' in m.group(2)):
            self.member_type = m.group(2)
        else:
            self.member_type = "attribute (%s)" % str(type(self.member))

    def compute_privacy(self):
        r"""
        Compute member privacy, if any.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('__class__', parent=p)
            sage: m.compute_privacy()
            sage: m.privacy
            'python_special'
            sage: m = ExploredMember('_doccls', parent=p)
            sage: m.compute_privacy()
            sage: m.privacy
            'private'
        """
        if not self.name.startswith('_'):
            self.privacy = None
            return
        if self.name.startswith('__') and self.name.endswith('__'):
            self.privacy = 'python_special'
        elif self.name.startswith('_') and self.name.endswith('_'):
            self.privacy = 'sage_special'
        else:
            self.privacy = 'private'

    def compute_origin(self, parent=None):
        r"""
        Determine in which base class 'origin' of class 'parent'
        this member is actually defined, and also return the list
        of overrides if any.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('_reduction', parent=p)
            sage: m.compute_origin()
            sage: m.origin, m.overrides
            (<class 'sage.combinat.partition.Partitions_all_with_category.element_class'>,
             [<class 'sage.categories.infinite_enumerated_sets.InfiniteEnumeratedSets.element_class'>,
              <class 'sage.categories.enumerated_sets.EnumeratedSets.element_class'>,
              <class 'sage.categories.sets_cat.Sets.Infinite.element_class'>,
              <class 'sage.categories.sets_cat.Sets.element_class'>,
              <class 'sage.categories.sets_with_partial_maps.SetsWithPartialMaps.element_class'>,
              <class 'sage.categories.objects.Objects.element_class'>])
        """
        if not parent:
            if not hasattr(self, 'parent'):
                raise ValueError("Cannot compute origin without a parent.")
            parent = self.parent
        self.parent = parent
        if isclass(parent):
            parentclass = parent
        else:
            parentclass = parent.__class__
        origin, overrides = parentclass, []
        for c in parentclass.__mro__[1:]:
            if not self.name in [x[0] for x in getmembers(c)]:
                continue
            for x in getmembers(c):
                if x[0] == self.name:
                    if x[1] == getattr(parentclass, self.name):
                        origin = c
                    else:
                        overrides.append(c)
        self.origin, self.overrides = origin, overrides

    def compute_argspec(self, parent=None):
        r"""
        If this member is a method: compute its args and defaults.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: p = Partition([3,3,2,1])
            sage: m = ExploredMember('add_cell', parent=p)
            sage: m.compute_member()
            sage: m.compute_argspec()
            sage: m.args, m.defaults
            (['self', 'i', 'j'], (None,))
        """
        args = None
        defaults = None
        try:
            argspec = getargspec(self.member)
            if hasattr(argspec, 'args'):
                self.args = argspec.args
            if hasattr(argspec, 'defaults'):
                self.defaults = argspec.defaults
        except:
            pass

    def compute_property_label(self, config):
        r"""
        Retrieve the property label, if any, from configuration 'config'.

        TESTS::
            sage: from new_sage_explorer.explored_member import ExploredMember
            sage: from sage.combinat.partition import Partition
            sage: F = GF(7)
            sage: m = ExploredMember('polynomial', parent=F)
            sage: m.compute_property_label({'polynomial': {'in': 'Fields.Finite'}})
            sage: m.prop_label
            'Polynomial'
        """
        self.prop_label = None
        if not self.name in config.keys():
            return
        if not hasattr(self, 'parent'):
            raise ValueError("Cannot compute property label without a parent.")
        myconfig = config[self.name]
        if 'isinstance' in myconfig.keys():
            """Test isinstance"""
            if not isinstance(self.parent, eval_in_main(myconfig['isinstance'])):
                return
        if 'not isinstance' in myconfig.keys():
            """Test not isinstance"""
            if isinstance(self.parent, eval_in_main(myconfig['not isinstance'])):
                return
        if 'in' in myconfig.keys():
            """Test in"""
            try:
                if not self.parent in eval_in_main(myconfig['in']):
                    return
            except:
                return # The error is : descriptor 'category' of 'sage.structure.parent.Parent' object needs an argument
        if 'not in' in myconfig.keys():
            """Test not in"""
            if self.parent in eval_in_main(myconfig['not in']):
                return
        def test_when(funcname, expected, operator=None, complement=None):
            if funcname == 'isclass': # FIXME Prendre les premières valeurs de obj.getmembers pour le test -> calculer cette liste avant ?
                res = eval_in_main(funcname)(self.parent)
            else:
                res = getattr(self.parent, funcname).__call__()
            if operator and complement:
                res = operator(res, eval_in_main(complement))
            return (res == expected)
        def split_when(s):
            when_parts = myconfig['when'].split()
            funcname = when_parts[0]
            if len(when_parts) > 2:
                operatorsign, complement = when_parts[1], when_parts[2]
            elif len(when_parts) > 1:
                operatorsign, complement = when_parts[1][0], when_parts[1][1:]
            if operatorsign in OPERATORS.keys():
                operator = OPERATORS[operatorsign]
            else:
                operator = "not found"
            return funcname, operator, complement
        if 'when' in myconfig.keys():
            """Test when predicate(s)"""
            if isinstance(myconfig['when'], six.string_types):
                when = [myconfig['when']]
            elif isinstance(myconfig['when'], (list,)):
                when = myconfig['when']
            else:
                return
            for predicate in when:
                if not ' ' in predicate:
                    if not hasattr(self.parent, predicate):
                        return
                    if not test_when(predicate, True):
                        return
                else:
                    funcname, operator, complement = split_when(predicate)
                    if not hasattr(self.parent, funcname):
                        return
                    if operator == "not found":
                        return
                    if not test_when(funcname, True, operator, complement):
                        return
        if 'not when' in myconfig.keys():
            """Test not when predicate(s)"""
            if isinstance(myconfig['not when'], six.string_types):
                nwhen = [myconfig['not when']]
            if not test_when(myconfig['not when'],False):
                return
            elif isinstance(myconfig['not when'], (list,)):
                nwhen = myconfig['not when']
            else:
                return
            for predicate in nwhen:
                if not ' ' in predicate:
                    if not test_when(predicate, False):
                        return
                else:
                    funcname, operator, complement = split_when(predicate)
                    if not test_when(funcname, False, operator, complement):
                        return
        if 'label' in myconfig.keys():
            self.prop_label = myconfig['label']
        else:
            self.prop_label = ' '.join([x.capitalize() for x in self.name.split('_')])


@lru_cache(maxsize=100)
def get_members(cls):
    r"""
    Get all members for a class.

    INPUT: ``cls`` a Sage class.
    OUTPUT: List of `Member` named tuples.

    TESTS::

        sage: from new_sage_explorer.explored_member import get_members
        sage: from sage.combinat.partition import Partition
        sage: mm = get_members(Partition)
        sage: mm[2].name, mm[2].privacy
        ('__class__', 'python_special')
        sage: [(mm[i].name, mm[i].overrides, mm[i].privacy) for i in range(len(mm)) if mm[i].name == '_unicode_art_']
        [('_unicode_art_',
         [<class 'sage.combinat.combinat.CombinatorialElement'>,
          <class 'sage.combinat.combinat.CombinatorialObject'>,
          <class 'sage.structure.element.Element'>,
          <class 'sage.structure.sage_object.SageObject'>],
         'sage_special')]
        sage: from sage.combinat.tableau import Tableau
        sage: mm = get_members(Tableau([[1], [2], [3]]))
        sage: [(mm[i].name, mm[i].parent, mm[i].origin, mm[i].prop_label) for i in range(len(mm)) if mm[i].name == 'conjugate']
        [('conjugate', [[1], [2], [3]], <class 'sage.combinat.tableau.Tableau'>, 'Conjugate')]
    """
    members = []
    for name, member in getmembers(cls):
        if isabstract(member) or 'deprecated' in str(type(member)).lower():
            continue
        m = ExploredMember(name, member=member, parent=cls)
        m.compute_member_type()
        m.compute_origin()
        m.compute_privacy()
        m.compute_property_label(CONFIG_PROPERTIES)
        members.append(m)
    return members

@lru_cache(maxsize=500)
def get_properties(obj):
    r"""
    Get all properties for an object.

    INPUT: ``obj`` a Sage object.
    OUTPUT: List of `Member` named tuples.

    TESTS::

        sage: from new_sage_explorer.explored_member import get_properties
        sage: from sage.combinat.tableau import *
        sage: st = StandardTableaux(3).an_element()
        sage: sst = SemistandardTableaux(3).an_element()
        sage: pp = get_properties(st)
        sage: pp[3].name, pp[3].prop_label
        ('parent', 'Element of')
        sage: pp = get_properties(sst)
        sage: pp[3].name, pp[3].prop_label
        ('is_standard', 'Is Standard')
    """
    try:
        members = getmembers(obj)
    except:
        return [] # Can be a numeric value ..
    properties = []
    #if isclass(obj):
    #    cls = obj
    #else:
    #    cls = obj.__class__
    for name, member in members:
        if isabstract(member) or 'deprecated' in str(type(member)).lower():
            continue
        m = ExploredMember(name, member=member, parent=obj)
        m.compute_property_label(CONFIG_PROPERTIES)
        if m.prop_label:
            properties.append(m)
    return properties
