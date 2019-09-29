#!/usr/bin/python
import re
import sys
import os.path

from definition import *
from string import Template


# Converts text in 'CamelCase' into 'CAMEL_CASE'
# Snippet taken from: http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
def convertToUnderscore(s):
    return re.sub('(?!^)([0-9A-Z]+)', r'_\1', s).upper().replace('__', '_')


def convertToCamelCase(s):
    result = ''
    begin = True
    for c in s:
        if c == '_':
            begin = True
        elif begin:
            result += c.upper()
            begin = False
        else:
            result += c
    return result


def nameListToString(nameList):
    nameString = ''
    for name in nameList:
        if len(nameString) > 0:
            nameString += ' '
        nameString += name
    return nameString


class MakePharoBindingsVisitor:
    def __init__(self, outputDirectory, apiDefinition, forSqueak = False):
        self.outputDirectory = outputDirectory
        self.out = None
        self.variables = {}
        self.constants = {}
        self.typeBindings = {}
        self.interfaceTypeMap = {}
        self.forSqueak = forSqueak
        self.targetLanguage = 'Pharo'
        if forSqueak:
            self.targetLanguage = 'Squeak'

        self.namespacePrefix = apiDefinition.getBindingProperty(self.targetLanguage, 'namespacePrefix')
        self.interfaceBaseClassName = self.namespacePrefix + 'Interface'
        self.cbindingsBaseClassName = self.namespacePrefix + 'CBindingsBase'

        self.generatedCodeCategory = apiDefinition.getBindingProperty(self.targetLanguage, 'package')
        self.constantsClassName = self.namespacePrefix + 'Constants'
        self.typesClassName = self.namespacePrefix + 'Types'
        self.cbindingsClassName = self.namespacePrefix + 'CBindings'
        self.doItClassName = self.namespacePrefix
        self.startedExtensions = set()
        self.bindingsPoolDictionaries = [self.constantsClassName, self.typesClassName]
        self.externalStructureSuperClass = 'FFIExternalStructure'
        self.externalUnionSuperClass = 'FFIExternalUnion'

        if forSqueak:
            self.bindingsPoolDictionaries = [self.constantsClassName]
            self.externalStructureSuperClass = apiDefinition.getBindingProperty('Squeak', 'externalStructureSuperClass')
            self.externalUnionSuperClass = apiDefinition.getBindingProperty('Squeak', 'externalUnionSuperClass')

    def processText(self, text, **extraVariables):
        t = Template(text)
        return t.substitute(**dict(self.variables.items() + extraVariables.items()))

    def write(self, text):
        self.out.write(text)

    def writeLine(self, line):
        self.write(line)
        self.newline()

    def newline(self):
        self.write('\n')

    def printString(self, text, **extraVariables):
        self.write(self.processText(text, **extraVariables))

    def printLine(self, text, **extraVariables):
        self.write(self.processText(text, **extraVariables))
        self.newline()

    def visitApiDefinition(self, api):
        self.setup(api)
        self.processVersions(api.versions)
        try:
            self.emitBindings(api)
        finally:
            self.finishCurrentFile()

    def setup(self, api):
        self.api = api
        self.variables = {
            'ConstantPrefix': api.constantPrefix,
            'FunctionPrefix': api.functionPrefix,
            'TypePrefix': api.typePrefix,
        }

    def visitEnum(self, enum):
        for constant in enum.constants:
            cname = self.processText("$ConstantPrefix$ConstantName", ConstantName=convertToUnderscore(constant.name))
            self.constants[cname] = constant.value
        cenumName = self.processText("$TypePrefix$EnumName", EnumName=enum.name)
        if self.forSqueak:
            self.typeBindings[cenumName] = 'long'
        else:
            self.typeBindings[cenumName] = '#int'

    def visitTypedef(self, typedef):
        mappingType = typedef.ctype
        if mappingType.startswith('const '):
            mappingType = mappingType[len('const '):]

        if self.forSqueak:
            mappingType = mappingType.replace('long', 'longlong').replace('int', 'long').replace('char', 'byte')
        if mappingType.startswith('unsigned '):
            mappingType = 'u' + mappingType[len('unsigned '):]

        if mappingType.startswith('signed '):
            mappingType = mappingType[len('signed '):]

        if self.forSqueak:
            if mappingType.startswith('uchar') or mappingType.startswith('ubyte'):
                mappingType = mappingType[1:]

        typedefName = self.processText("$TypePrefix$Name", Name=typedef.name)
        if self.forSqueak:
            self.typeBindings[typedefName] = mappingType
        else:
            self.typeBindings[typedefName] = "#'" + mappingType + "'"

    def visitInterface(self, interface):
        cname = typedefName = self.processText("$TypePrefix$Name", Name=interface.name)
        self.interfaceTypeMap[interface.name + '*'] = self.namespacePrefix + convertToCamelCase(interface.name)
        if self.forSqueak:
            self.typeBindings[cname] = "void"
        else:
            self.typeBindings[cname] = "#'void'"

    def processFragment(self, fragment):
        # Visit the constants.
        for constant in fragment.constants:
            constant.accept(self)

        # Visit the types.
        for type in fragment.types:
            type.accept(self)

        # Visit the interfaces.
        for interface in fragment.interfaces:
            interface.accept(self)

    def processVersion(self, version):
        self.processFragment(version)

    def processVersions(self, versions):
        for version in versions.values():
            self.processVersion(version)

    def finishCurrentFile(self):
        if self.out is not None:
            self.out.close()
        self.out = None

    def ensureFolderExists(self, path):
        if not os.path.isdir(path):
            if os.path.exists(path):
                raise Exception("Cannot create directory " + path)
            os.mkdir(path)

    def ensureCategoryFolder(self, category):
        folderName = os.path.join(self.outputDirectory, category)
        self.ensureFolderExists(self.outputDirectory)
        self.ensureFolderExists(folderName)
        return folderName

    def beginFileInCategory(self, category, fileName):
        folder = self.ensureCategoryFolder(category)
        self.out = open(os.path.join(folder, fileName), "w")
        self.outFileName = fileName

    def emitPackageFile(self, package):
        self.beginFileInCategory(package, 'package.st')
        self.printLine("Package { #name : #'$PackageName' }", PackageName=package)

    def beginClassFile(self, category, className):
        self.finishCurrentFile()
        self.beginFileInCategory(category, className + '.class.st')

    def beginClassFileAppending(self, category, className, isExtension=False):
        folder = self.ensureCategoryFolder(category)
        if isExtension:
            fileName = os.path.join(folder, className + '.extension.st')
        else:
            fileName = os.path.join(folder, className + '.class.st')

        if self.outFileName != fileName:
            self.finishCurrentFile()
            if isExtension and (className not in self.startedExtensions):
                self.out = open(fileName, "w")
            else:
                self.out = open(fileName, "a")
            self.outFileName = fileName

            if isExtension and (className not in self.startedExtensions):
                self.printLine('Extension { #name : #$ClassName }', ClassName=className)
                self.newline()
                self.startedExtensions.add(className)

    def emitTonelStringList(self, varName, stringList):
        if len(stringList) == 0:
            return

        self.printLine("\t#$VarName : [", VarName=varName)
        i = 0
        while i < len(stringList):
            comma = ''
            if i + 1 < len(stringList):
                comma = ','
            self.printLine("\t\t'$String'$Comma", String=stringList[i], Comma=comma)
            i += 1
        self.printLine("\t],")

    def emitSubclass(self, baseClass, className, instanceVariableNames=[], classVariableNames=[], poolDictionaries=[]):
        self.beginClassFile(self.generatedCodeCategory, className)

        self.printLine('Class {')
        self.printLine('\t#name : #$ClassName,', ClassName=className)
        self.emitTonelStringList('instVars', instanceVariableNames)
        self.emitTonelStringList('classVars', classVariableNames)
        self.emitTonelStringList('pools', poolDictionaries)
        self.printLine('\t#superclass : #$BaseClass,', BaseClass=baseClass)
        self.printLine("\t#category : '$Category'", Category=self.generatedCodeCategory)
        self.printLine('}')
        self.newline()

    def emitConstants(self):
        self.emitSubclass('SharedPool', self.constantsClassName, [], list(self.constants.keys()))
        self.beginMethod(self.constantsClassName + ' class', 'initialize', 'initialize')
        self.printLine('"')
        self.printLine('\tself initialize')
        self.printLine('"')
        self.printLine('\tsuper initialize.')
        self.newline()
        if self.forSqueak:
             self.printString(
"""
    self data pairsDo: [:k :v |
        self classPool at: k put: v
    ]
""")
        else:
            self.printString(
"""
    self data pairsDo: [:k :v |
        self writeClassVariableNamed: k value: v
    ]
""")
        self.endMethod()

        self.beginMethod(self.constantsClassName + ' class', 'initialization', 'data')
        self.printLine('\t^ #(')
        for constantName in self.constants.keys():
            constantValue = self.constants[constantName]
            if constantValue.startswith('0x'):
                constantValue = '16r' + constantValue[2:]
            self.printLine("\t\t$ConstantName $ConstantValue", ConstantName=constantName, ConstantValue=constantValue)
        self.printLine('\t)')
        self.endMethod()

    def isValidIdentCharacter(self, character):
        return ('a' <= character and character <= 'z') or \
               ('A' <= character and character <= 'Z') or \
               ('0' <= character and character <= '9') or \
               character == '_'

    def makeFullTypeName(self, rawTypeName):
        baseTypeNameSize = 0
        for i in range(len(rawTypeName)):
            if self.isValidIdentCharacter(rawTypeName[i]):
                baseTypeNameSize = i + 1
            else:
                break

        baseTypeName = rawTypeName[0:baseTypeNameSize]
        typeDecorators = rawTypeName[baseTypeNameSize:]
        mappedBaseType = self.typeBindings[baseTypeName]
        #print "'%s' %d '%s' '%s' -> '%s'" % (rawTypeName, baseTypeNameSize, baseTypeName, typeDecorators, mappedBaseType);
        return mappedBaseType + typeDecorators

    def makeFullTypeNameWithPrefix(self, rawTypeName):
        return self.makeFullTypeName(self.api.typePrefix + rawTypeName)

    def emitTypeBindings(self):
        if self.forSqueak:
            return

        self.emitSubclass('SharedPool', self.typesClassName, [], list(self.typeBindings.keys()))
        self.beginMethod(self.typesClassName + ' class', 'initialize', 'initialize')
        self.printLine('"')
        self.printLine('\tself initialize')
        self.printLine('"')
        self.printLine('\tsuper initialize.')
        self.newline()

        for ctypeName in self.typeBindings.keys():
            pharoName = self.typeBindings[ctypeName]
            self.printLine('\t$CTypeName := $PharoName.', CTypeName=ctypeName, PharoName=pharoName)
        self.endMethod()

    def emitCBindings(self, api):
        self.emitSubclass(self.cbindingsBaseClassName, self.cbindingsClassName, [], [], self.bindingsPoolDictionaries)

        for version in api.versions.values():
            # Emit the methods of the interfaces.
            for interface in version.interfaces:
                self.emitInterfaceCBindings(interface)

            # Emit the global c functions
            self.emitCGlobals(version.globals)

    def emitInterfaceCBindings(self, interface):
        for method in interface.methods:
            self.emitCMethodBinding(method, interface.name)

    def emitCGlobals(self, globals):
        for method in globals:
            self.emitCMethodBinding(method, 'global c functions')

    def emitCMethodBinding(self, method, category):

        selector = method.name
        allArguments = method.arguments
        if method.clazz is not None:
            allArguments = [SelfArgument(method.clazz)] + allArguments

        first = True
        for arg in allArguments:
            if first:
                selector += '_'
                first = False
            else:
                selector += ' '

            name = arg.name
            if name == 'self':
                name = 'selfObject'
            selector += name + ': ' + name

        self.beginMethod(self.cbindingsClassName, category, selector)
        if self.forSqueak:
           self.printString("\t<cdecl: $ReturnType '$FunctionPrefix$FunctionName' (",
                ReturnType=self.makeFullTypeNameWithPrefix(method.returnType),
                FunctionName=method.cname)
        else:
            self.printString("\t^ self ffiCall: #($TypePrefix$ReturnType $FunctionPrefix$FunctionName (",
                ReturnType=method.returnType,
                FunctionName=method.cname)

        first = True
        for arg in allArguments:
            if first:
                first = False
            else:
                if self.forSqueak:
                    self.printString(' ')
                else:
                    self.printString(' , ')

            name = arg.name
            if name == 'self':
                name = 'selfObject'
            argTypeString = arg.type
            if (arg.arrayReturn or arg.pointerList) and argTypeString.endswith('**'):
                argTypeString = argTypeString[:-1]
            if self.forSqueak:
                self.printString("$ArgType", ArgType=self.makeFullTypeNameWithPrefix(argTypeString), ArgName=name)
            else:
                self.printString("$TypePrefix$ArgType $ArgName", ArgType=argTypeString, ArgName=name)

        if self.forSqueak:
            self.printLine(")>")
            self.printLine("\t^ self externalCallFailed")
        else:
            self.printLine(") )")
        self.endMethod()

    def emitInterfaceClasses(self, api):
        for version in api.versions.values():
            for interface in version.interfaces:
                pharoName = self.namespacePrefix + convertToCamelCase(interface.name)
                self.emitSubclass(self.interfaceBaseClassName, pharoName)

    def emitAggregate(self, aggregate):
        cname = self.processText("$TypePrefix$AggregateName", AggregateName=aggregate.name)
        pharoName = self.namespacePrefix + convertToCamelCase(aggregate.name)
        self.typeBindings[cname] = pharoName
        superClass = self.externalStructureSuperClass
        if aggregate.isUnion():
            superClass = self.externalUnionSuperClass

        self.emitSubclass(superClass, pharoName, [], [], self.bindingsPoolDictionaries)

        if self.forSqueak:
            self.beginMethod(pharoName + ' class', 'definition', 'fields')
            self.printLine(
"""	"
	self defineFields
	"
    ^ #(""")
            for field in aggregate.fields:
                self.printLine("\t\t($FieldName '$FieldType')", FieldType=self.makeFullTypeNameWithPrefix(field.type), FieldName=field.name)
        else:
            self.beginMethod(pharoName + ' class', 'definition', 'fieldsDesc')
            self.printLine(
"""	"
	self rebuildFieldAccessors
	"
    ^ #(""")
            for field in aggregate.fields:
                self.printLine("\t\t $TypePrefix$FieldType $FieldName;", FieldType=field.type, FieldName=field.name)

        self.printLine("\t)")
        self.endMethod()

    def emitAggregates(self, api):
        for version in api.versions.values():
            for struct in version.agreggates:
                self.emitAggregate(struct)

    def emitPoolInitializations(self, api, doItClassName):
        self.beginMethod(doItClassName + ' class', 'initialization', 'initializeConstants')
        self.printLine("\t<script>")
        if not self.forSqueak:
            self.printLine("\t$Types initialize.", Types=self.typesClassName)
        self.printLine("\t$Constants initialize.", Constants=self.constantsClassName)
        self.endMethod()

    def emitAggregatesInitializations(self, api, doItClassName):
        self.beginMethod(doItClassName + ' class', 'initialization', 'initializeStructures')
        self.printLine("\t<script>")
        for version in api.versions.values():
            for struct in version.agreggates:
                pharoName = self.namespacePrefix + convertToCamelCase(struct.name)
                if self.forSqueak:
                    self.printLine('\t$Structure defineFields.', Structure=pharoName)
                else:
                    self.printLine('\t$Structure rebuildFieldAccessors.', Structure=pharoName)
        self.endMethod()

    def emitBindingsInitializations(self, api, doItClassName):
        self.beginMethod(doItClassName + ' class', 'initialization', 'initializeBindings')
        self.printLine("\t<script>")
        self.printLine("\tself initializeConstants.")
        self.printLine("\tself initializeStructures.")
        self.endMethod()

    def emitDoIts(self, api, doItClassName):
        self.emitSubclass('Object', doItClassName)
        self.emitPoolInitializations(api, doItClassName)
        self.emitAggregatesInitializations(api, doItClassName)
        self.emitBindingsInitializations(api, doItClassName)

    def emitBaseClasses(self, api):
        self.emitPackageFile(self.generatedCodeCategory)
        self.emitConstants()
        self.emitInterfaceClasses(api)
        self.emitAggregates(api)
        self.emitTypeBindings()
        self.emitCBindings(api)
        self.emitPharoBindings(api)

        self.emitDoIts(api, self.namespacePrefix + 'GeneratedDoIt')

    def emitPharoBindings(self, api):
        for version in api.versions.values():
            for interface in version.interfaces:
                self.emitInterfaceBindings(interface)
            self.emitGlobals(version.globals)

    def emitInterfaceBindings(self, interface):
        for method in interface.methods:
            self.emitMethodWrapper(method)

    def emitGlobals(self, globals):
        for method in globals:
            self.emitMethodWrapper(method)

    def emitMethodWrapper(self, method):
        ownerClass = self.namespacePrefix
        clazz = method.clazz
        allArguments = method.arguments
        category = '*' + self.generatedCodeCategory
        if clazz is not None:
            ownerClass = self.namespacePrefix + convertToCamelCase(clazz.name)
            allArguments = [SelfArgument(method.clazz)] + allArguments
            category = 'wrappers'

        methodName = method.name
        if methodName == 'release':
            methodName = 'primitiveRelease'

        # Build the method selector.
        first = True
        for arg in method.arguments:
            name = arg.name
            if first:
                first = False
                methodName += ": " + name
            else:
                methodName += " " + name + ": " + name

        self.beginMethodAppendingFile(ownerClass, category, methodName)

        # Temporal variable for the return value
        self.printLine("\t| resultValue_ |")

        # Call the c bindings.
        self.printString("\tresultValue_ := $CBindingsClass uniqueInstance $MethodName", CBindingsClass=self.cbindingsClassName, MethodName=method.name)
        first = True
        for arg in allArguments:
            name = arg.name
            if name == 'self':
                name = 'selfObject'
            value = name

            if arg.type in self.interfaceTypeMap:
                value = self.processText("(self validHandleOf: $ArgName)", ArgName=name)

            if first:
                if first and clazz is not None:
                    self.printString('_$ArgName: (self validHandle)', ArgName=name)
                else:
                    self.printString('_$ArgName: $ArgValue', ArgName=name, ArgValue=value)
                first = False
            else:
                self.printString(' $ArgName: $ArgValue', ArgName=name, ArgValue=value)
        self.printLine('.')

        if method.returnType in self.interfaceTypeMap:
            self.printLine('\t^ $InterfaceWrapper forHandle: resultValue_', InterfaceWrapper=self.interfaceTypeMap[method.returnType])
        elif method.returnType == 'error':
            self.printLine('\tself checkErrorCode: resultValue_')
        else:
            self.printLine('\t^ resultValue_')

        self.endMethod()

    def emitBindings(self, api):
        self.emitBaseClasses(api)

    def beginMethod(self, className, category, methodHeader):
        self.printLine("{ #category : #'$Category' }", Category=category)
        self.printLine("$ClassName >> $MethodHeader [", ClassName=className, MethodHeader=methodHeader)

    def beginMethodAppendingFile(self, className, category, methodHeader):
        self.beginClassFileAppending(self.generatedCodeCategory, className, category.startswith('*'))
        self.beginMethod(className, category, methodHeader)

    def endMethod(self):
        self.printLine("]")
        self.newline()


def main():
    arguments = sys.argv[1:]
    if len(arguments) < 2:
        print "make-headers [-squeak] <definitions> <output dir>"
        return

    forSqueak = False
    if arguments[0] == '-squeak':
        arguments = arguments[1:]
        forSqueak = True

    api = ApiDefinition.loadFromFileNamed(arguments[0])
    visitor = MakePharoBindingsVisitor(arguments[1], api, forSqueak)
    api.accept(visitor)

if __name__ == '__main__':
    main()
