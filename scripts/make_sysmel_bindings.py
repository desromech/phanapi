#!/usr/bin/python3
import re
import sys
import os.path

from definition import *
from string import Template

OUTPUT_HEADER = """
namespace $Namespace definition:
{

template SmartRefPtr(PT: Type)
    := struct definition: {
    compileTime constant PointedType := PT.
    compileTime constant PointerType := PointedType pointer.
    compileTime constant SmartPointerType := SelfType.

    private field pointer_ type: PointerType.

    meta extend: {
        inline method for: (pointer: PointerType) ::=> SmartPointerType
            := SmartPointerType basicNewValue initializeWith: pointer; yourself.
        macro method nil := ``(`,self basicNewValue).
    }.

    inline method finalize => Void := {
        if: pointer_ ~~ nil then: {
            pointer_ _ release.
        }.
    }.

    inline method initializeWith: (pointer: PointerType) ::=> Void := {
        pointer_ := pointer
    }.

    inline method initializeCopyingFrom: (o: SelfType const ref) ::=> Void := {
        pointer_ := o __private pointer_.
        if: pointer_ ~~ nil then: {
            pointer_ _ addReference
        }.
    }.

    inline method initializeMovingFrom: (o: SelfType tempRef) ::=> Void := {
        pointer_ := o __private pointer_.
        o __private pointer_ := nil
    }.

    inline const method _ => PointedType ref
        := pointer_ _.

    inline const method getPointer => PointerType
        := pointer_.

    inline method reset: (newPointer: PointerType) ::=> Void := {
        if: pointer_ ~~ nil then: {
            pointer_ _ release
        }.

        pointer_ := newPointer
    }.

    inline method reset => Void
        :=  self reset: nil.

    inline method assignValue: (o: SelfType const ref) ::=> SelfType const ref := {
        let newPointer := o __private pointer_.
        if: newPointer ~~ nil then: {
            newPointer _ addReference
        }.
        if: pointer_ ~~ nil then: {
            pointer_ _ release
        }.

        pointer_ := newPointer.
        self
    }.

    inline method assignValue: (o: SelfType tempRef) ::=> SelfType const ref := {
        let newPointer := o __private pointer_.
        o __private pointer_ := nil.
        if: pointer_ ~~ nil then: {
            pointer_ _ release
        }.

        pointer_ := newPointer.
        self
    }.

    ## Some convenience macros.
    macro method isNil := ``(`,self getPointer isNil).
    macro method isNotNil := ``(`,self getPointer isNotNil).

    macro method ifNil: nilAction := ``(`,self getPointer ifNil: `,nilAction).
    macro method ifNil: nilAction ifNotNil: notNilAction := ``(`,self getPointer ifNil: `,nilAction ifNotNil: `, notNilAction).
    macro method ifNotNil: notNilAction := ``(`,self getPointer ifNotNil: `,notNilAction).
    macro method ifNotNil: notNilAction ifNil: nilAction  := ``(`,self getPointer ifNotNil: `,notNilAction ifNil: `,nilAction).
}.

"""

OUTPUT_FOOTER = """

inline method throwIfError: (errorCode: Error) ::=> Void := {
    if: errorCode value < 0 then: {
        ##StdNative stderr << "Got error code in binding call " << errorCode value; nl.
        ##StdNative abort().
    }.
}.

}. ## End of namespace $Namespace
"""

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

def convertToLowCamelCase(s):
    result = ''
    begin = True
    first = True
    for c in s:
        if c == '_':
            begin = True
        elif begin:
            if not first:
                result += c.upper()
            else:
                result += c
            begin = False
            first = False
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


class MakeSysmelBindingsVisitor:
    def __init__(self, outputFileName, apiDefinition):
        self.out = open(outputFileName, "w")
        self.outFileName = outputFileName
        self.variables = {}
        self.enums = {}
        self.typeBindings = {}
        self.interfaceTypeMap = {}
        self.targetLanguage = 'Sysmel'

        self.namespace = apiDefinition.getBindingProperty(self.targetLanguage, 'namespace')
        self.startedExtensions = set()

    def processText(self, text, **extraVariables):
        t = Template(text)
        return t.substitute(**dict(list(self.variables.items()) + list(extraVariables.items())))

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

    def printHR(self):
        self.printLine("#"*80)

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
        enumTypeName = convertToCamelCase(enum.name);
        self.enums[enumTypeName] = enum
        cenumName = enum.name
        self.typeBindings[cenumName] = enumTypeName

    def visitTypedef(self, typedef):
        self.typeBindings[typedef.name] = typedef.sysmelType

    def visitInterface(self, interface):
        cname = interface.name
        interfaceName = convertToCamelCase(interface.name)
        self.interfaceTypeMap[interface.name + '*'] = interfaceName + " pointer"
        self.typeBindings[cname] = interfaceName

    def visitStruct(self, aggregate):
        cname = aggregate.name
        structName = convertToCamelCase(aggregate.name)
        self.typeBindings[cname] = structName

    def visitUnion(self, aggregate):
        self.visitStruct(aggregate)

    def processFragment(self, fragment):
        # Visit the constants.
        for constant in fragment.constants:
            constant.accept(self)

        # Visit the types.
        for type in fragment.types:
            type.accept(self)

        for aggregate in fragment.agreggates:
            aggregate.accept(self)

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

    def emitTypeDefs(self):
        pass

    def emitInterfaceDeclarations(self, api):
        self.printHR()
        self.printLine("## Interface declarations.")
        self.printHR()

        for version in api.versions.values():
            for interface in version.interfaces:
                self.printLine("class $InterfaceName definition: {}.", InterfaceName=convertToCamelCase(interface.name))
        self.newline()

    def emitEnums(self):
        self.printHR()
        self.printLine("## Enums.")
        self.printHR()

        for enumName in self.enums.keys():
            enum = self.enums[enumName]
            self.printLine("enum $Name valueType: Int32; values: #{", Name=enumName)
            for constant in enum.constants:
                constantValue = constant.value
                constantName = constant.name
                if enum.optionalPrefix is not None and constantName.startswith(enum.optionalPrefix):
                    constantName = constantName[len(enum.optionalPrefix):]
                if enum.optionalSuffix is not None and constantName.endswith(enum.optionalSuffix):
                    constantName = constantName[:-len(enum.optionalSuffix)]
                if constantValue.startswith('0x'):
                    constantValue = '16r' + constantValue[2:]
                self.printLine("\t$Name: $Value.", Name=constantName, Value=constantValue)
            self.printLine("}.")
            self.newline()


    def emitAggregate(self, aggregate):
        kind = "struct"
        if aggregate.isUnion():
            kind = "union"
        name = convertToCamelCase(aggregate.name)
        self.printLine("$AggregateKind $Name definition: {", AggregateKind=kind, Name=name)
        for field in aggregate.fields:
            self.printLine("\tpublic field $FieldName type: $FieldType.", FieldType=self.makeFullTypeName(field.type), FieldName=field.name)

        self.printLine("}.")
        self.newline()

    def emitAggregates(self, api):
        for version in api.versions.values():
            for struct in version.agreggates:
                self.emitAggregate(struct)

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
        typeDecorators = rawTypeName[baseTypeNameSize:].replace('*', ' pointer')
        mappedBaseType = self.typeBindings[baseTypeName]
        #print "'%s' %d '%s' '%s' -> '%s'" % (rawTypeName, baseTypeNameSize, baseTypeName, typeDecorators, mappedBaseType);
        return mappedBaseType + typeDecorators

    def emitCBindings(self, api):
        self.printHR()
        self.printLine("## The exported C API functions.")
        self.printHR()

        for version in api.versions.values():
            # Emit the global c functions
            self.emitCGlobals(version.globals)

            # Emit the methods of the interfaces.
            for interface in version.interfaces:
                self.emitInterfaceCBindings(interface)
        self.newline()

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

        self.printString("function $FunctionPrefix$FunctionName externC (", FunctionName=method.cname)

        first = True
        for arg in allArguments:
            if first:
                first = False
            else:
                self.printString(', ')

            name = arg.name
            if name == 'self':
                name = 'selfObject'
            argTypeString = self.makeFullTypeName(arg.type)
            self.printString("$ArgName: $ArgType", ArgType=argTypeString, ArgName=name)

        self.printLine(") => $ReturnType.", ReturnType=self.makeFullTypeName(method.returnType))

    def emitInterfaceClasses(self, api):
        for version in api.versions.values():
            for interface in version.interfaces:
                pharoName = self.namespacePrefix + convertToCamelCase(interface.name)
                self.emitSubclass(self.interfaceBaseClassName, pharoName)

    def emitSmartPointers(self, api):
        self.printHR()
        self.printLine("## Smart pointers.")
        self.printHR()
        for version in api.versions.values():
            for interface in version.interfaces:
                if interface.hasMethod('release') and interface.hasMethod('addReference'):
                    self.printLine("compileTime constant ${InterfaceName}Ref := SmartRefPtr($InterfaceName).", InterfaceName=convertToCamelCase(interface.name))

        self.newline()

    def emitObjectBindings(self, api):
        self.printHR()
        self.printLine("## Object bindings.")
        self.printHR()

        for version in api.versions.values():
            for interface in version.interfaces:
                self.emitInterfaceBindings(interface)

    def emitInterfaceBindings(self, interface):
        self.printLine('$Name extend: {', Name=convertToCamelCase(interface.name))
        for method in interface.methods:
            self.emitMethodWrapper(method)
        self.printLine('}.')
        self.newline()

    def convertMethodArgumentType(self, type):
        if type.endswith('**') and self.api.isInterfaceReference(type[:-1]):
            return self.makeFullTypeName(type[:-2]) + "Ref pointer"
        if self.api.isInterfaceReference(type):
            return self.makeFullTypeName(type[:-1]) + "Ref const ref"
        return self.makeFullTypeName(type)

    def convertMethodReturnType(self, type):
        if self.api.isInterfaceReference(type):
            return self.makeFullTypeName(type[:-1]) + "Ref"
        if type == "error":
            return "Void"
        return self.makeFullTypeName(type)

    def emitMethodWrapper(self, method):

        self.printString('\tinline method $Name', Name=method.name)

        # Build the method selector and the arguments.
        first = True
        for arg in method.arguments:
            name = arg.name
            selectorName = convertToLowCamelCase(name)
            type = self.convertMethodArgumentType(arg.type)
            if first:
                first = False
                self.printString(': ($ArgName: $ArgType)', ArgName=name, ArgType=type)
            else:
                self.printString(' $ArgSelectorName: ($ArgName: $ArgType)', ArgSelectorName=selectorName, ArgName=name, ArgType=type)

        returnType = self.convertMethodReturnType(method.returnType)
        self.printLine(' ::=> $ReturnType', ReturnType=returnType)

        # Build the wrapper prologue.
        hasEnclosingParentheses = False
        if method.returnType == "error" and not method.errorIsNotException:
            self.printString('\t\t:= throwIfError: (')
            hasEnclosingParentheses = True
        elif self.api.isInterfaceReference(method.returnType):
            self.printString('\t\t:= $ReturnType for: (', ReturnType=returnType)
            hasEnclosingParentheses = True
        else:
            self.printString('\t\t:= ')

        # Build the C function call.
        self.printString("$FunctionPrefix$FunctionName(", FunctionName=method.cname)

        # Emit the call arguments.
        clazz = method.clazz
        allArguments = method.arguments
        if clazz is not None:
            allArguments = [SelfArgument(method.clazz)] + allArguments

        first = True
        for arg in allArguments:
            convertedArgument = ""
            typeString = arg.type
            if typeString.endswith('**') and self.api.isInterfaceReference(typeString[:-1]):
                convertedArgument = self.processText('$Arg reinterpretCastTo: $Type', Arg = arg.name, Type=self.makeFullTypeName(typeString))
            elif self.api.isInterfaceReference(typeString):
                convertedArgument = arg.name + ' getPointer'
            else:
                convertedArgument = arg.name
            if first and clazz is not None:
                convertedArgument = "self address"

            if first:
                self.printString('$ArgValue', ArgValue=convertedArgument)
                first = False
            else:
                self.printString(', $ArgValue', ArgValue=convertedArgument)

        self.printString(")")

        # Build the wrapper epilogue.
        if hasEnclosingParentheses:
            self.printLine(').')
        else:
            self.printLine('.')
        self.newline()

    def emitBindings(self, api):
        self.printString(OUTPUT_HEADER, Namespace=self.namespace)
        self.emitTypeDefs()
        self.emitInterfaceDeclarations(api)
        self.emitEnums()
        self.emitAggregates(api)
        self.emitCBindings(api)
        self.emitSmartPointers(api)
        self.emitObjectBindings(api)
        self.printString(OUTPUT_FOOTER, Namespace=self.namespace)


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
        print("make-headers <definitions> <output dir>")
        return

    api = ApiDefinition.loadFromFileNamed(arguments[0])
    visitor = MakeSysmelBindingsVisitor(arguments[1], api)
    api.accept(visitor)

if __name__ == '__main__':
    main()
