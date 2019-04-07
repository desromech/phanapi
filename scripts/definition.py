from lxml import etree


def getOptionalAttribute(node, attr, default):
    if attr not in node.keys():
        return default
    return node.get(attr)


class Binding:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.properties = {}
        self.loadProperties(xmlNode)

    def getProperty(self, key):
        return self.properties[key]

    def loadProperties(self, xmlNode):
        for child in xmlNode:
            if child.tag == 'property':
                key = child.get('key')
                value = child.get('value')
                self.properties[key] = value

    def accept(self, visitor):
        return visitor.visitBindings(self)


class Typedef:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.ctype = xmlNode.get('ctype')

    def accept(self, visitor):
        return visitor.visitTypedef(self)


class Field:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.type = xmlNode.get('type')

    def accept(self, visitor):
        return visitor.visitField(self)


class Aggregate:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.fields = []
        self.loadFields(xmlNode)

    def loadFields(self, node):
        for child in node:
            if child.tag == 'field':
                self.fields.append(Field(child))

    def isStruct(self):
        return False

    def isUnion(self):
        return False

class Struct(Aggregate):
    def __init__(self, xmlNode):
        Aggregate.__init__(self, xmlNode)

    def accept(self, visitor):
        return visitor.visitStruct(self)

    def isStruct(self):
        return True

class Union(Aggregate):
    def __init__(self, xmlNode):
        Aggregate.__init__(self, xmlNode)

    def accept(self, visitor):
        return visitor.visitUnion(self)

    def isUnion(self):
        return True

class Enum:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.ctype = xmlNode.get('ctype')
        self.constants = []
        self.loadConstants(xmlNode)

    def accept(self, visitor):
        return visitor.visitEnum(self)

    def loadConstants(self, node):
        for child in node:
            if child.tag == 'constant':
                self.constants.append(Constant(child))


class Constant:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.type = getOptionalAttribute(xmlNode, 'type', 'int')
        self.value = xmlNode.get('value')

    def accept(self, visitor):
        return visitor.visitConstant(self)


class SelfArgument:
    def __init__(self, clazz):
        self.name = clazz.name
        self.type = clazz.name + '*'
        self.arrayReturn = False
        self.pointerList = False


class Argument:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.type = xmlNode.get('type')
        self.arrayReturn = getOptionalAttribute(xmlNode, 'arrayReturn', 'false') != 'false'
        self.pointerList = getOptionalAttribute(xmlNode, 'pointerList', 'false') != 'false'


class Function:
    def __init__(self, xmlNode, clazz = None):
        self.name = xmlNode.get('name')
        self.cname = getOptionalAttribute(xmlNode, 'cname', self.name)
        self.returnType = xmlNode.get('returnType')
        self.clazz = clazz
        self.arguments = []
        self.loadArguments(xmlNode)

    def accept(self, visitor):
        return visitor.visitFunction(self)

    def loadArguments(self, xmlNode):
        for child in xmlNode:
            if child.tag == 'arg':
                self.arguments.append(Argument(child))


class Interface:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')
        self.methods = []
        self.loadMethods(xmlNode)

    def accept(self, visitor):
        return visitor.visitInterface(self)

    def loadMethods(self, node):
        for child in node:
            if child.tag == 'method':
                self.methods.append(Function(child, self))


class ApiFragment:
    def __init__(self, xmlNode):
        self.name = xmlNode.get('name')

        self.types = []
        self.constants = []
        self.globals = []
        self.interfaces = []
        self.agreggates = []
        self.loadChildren(xmlNode)

    def getInterfaceNamesInto(self, dest):
        for iface in self.interfaces:
            dest.add(iface.name)

    def loadChildren(self, xmlNode):
        for child in xmlNode:
            if child.tag == 'types':
                self.loadTypes(child)
            elif child.tag == 'constants':
                self.loadConstants(child)
            elif child.tag == 'structs':
                self.loadStructs(child)
            elif child.tag == 'globals':
                self.loadGlobals(child)
            elif child.tag == 'interfaces':
                self.loadInterfaces(child)

    def loadTypes(self, node):
        for child in node:
            loadedNode = None
            if child.tag == 'typedef':
                loadedNode = Typedef(child)

            if loadedNode is not None:
                self.types.append(loadedNode)

    def loadConstants(self, node):
        for child in node:
            loadedNode = None
            if child.tag == 'enum': loadedNode = Enum(child)
            elif child.tag == 'constant' : loadedNode = Constant(child)

            if loadedNode is not None:
                self.constants.append(loadedNode)

    def loadStructs(self, node):
        for child in node:
            loadedNode = None
            if child.tag == 'struct': loadedNode = Struct(child)
            if child.tag == 'union': loadedNode = Union(child)

            if loadedNode is not None:
                self.agreggates.append(loadedNode)

    def loadGlobals(self, node):
        for child in node:
            loadedNode = None
            if child.tag == 'function': loadedNode = Function(child)

            if loadedNode is not None:
                self.globals.append(loadedNode)

    def loadInterfaces(self, node):
        for child in node:
            loadedNode = None
            if child.tag == 'interface': loadedNode = Interface(child)

            if loadedNode is not None:
                self.interfaces.append(loadedNode)

class ApiVersion(ApiFragment):
    def __init__(self, xmlNode):
        assert xmlNode.tag == 'version'
        ApiFragment.__init__(self, xmlNode)

class ApiExtension:
    def __init__(self, xmlNode):
        assert xmlNode.tag == 'extension'
        ApiFragment.__init__(self, xmlNode)

class ApiDefinition:
    def __init__(self, xmlNode):
        assert xmlNode.tag == 'api'
        self.bindings = {}
        self.versions = {}
        self.extensions = {}
        self.loadFragments(xmlNode)

        # TODO: Deprecate these
        self.name = xmlNode.get('name')
        self.headerFileName = self.getBindingProperty('C', 'headerFile')
        self.typePrefix = self.getBindingProperty('C', 'typePrefix')
        self.constantPrefix = self.getBindingProperty('C', 'constantPrefix')
        self.functionPrefix = self.getBindingProperty('C', 'functionPrefix')

        self.interfaceNameCache = None

    def accept(self, visitor):
        return visitor.visitApiDefinition(self)

    def getBindingProperty(self, language, key):
        return self.bindings[language].getProperty(key)

    def buildInterfaceNameCache(self):
        self.interfaceNameCache = set()
        for version in self.versions.values():
            version.getInterfaceNamesInto(self.interfaceNameCache)
        for extension in self.extensions.values():
            extension.getInterfaceNamesInto(self.interfaceNameCache)

    def getInterfaceNames(self):
        if self.interfaceNameCache is None:
            self.buildInterfaceNameCache()
        return self.interfaceNameCache

    def isInterfaceName(self, iname):
        return iname in self.getInterfaceNames()

    def isInterfaceReference(self, typeString):
        if typeString.endswith('*'):
            return self.isInterfaceName(typeString[:-1])
        return False

    @staticmethod
    def loadFromFileNamed(filename):
        tree = etree.parse(filename)
        return ApiDefinition(tree.getroot())

    def loadFragments(self, node):
        for c in node:
            if c.tag == 'version':
                version = ApiVersion(c)
                self.versions[version.name] = version
            elif c.tag == 'extensions':
                extension = ApiVersion(c)
                self.extensions[extension.name] = extension
            elif c.tag == 'bindings':
                self.loadBindings(c)

    def loadBindings(self, node):
        for child in node:
            loadedNode = None
            if child.tag == 'language':
                loadedNode = Binding(child)

            if loadedNode is not None:
                self.bindings[loadedNode.name] = loadedNode
