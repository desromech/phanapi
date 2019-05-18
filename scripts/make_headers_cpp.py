#!/usr/bin/python
import re
import sys

from definition import *
from string import Template


HEADER_START = \
"""
#ifndef $HeaderProtectMacro
#define $HeaderProtectMacro

#include <stdexcept>
#include "$CHeader"

/**
 * $ApiName exception.
 */
class ${TypePrefix}exception : public std::runtime_error
{
public:
    explicit ${TypePrefix}exception(${TypePrefix}error error)
        : std::runtime_error("$ApiName Error"), errorCode(error)
    {
    }

    ${TypePrefix}error getErrorCode() const
    {
        return errorCode;
    }

private:
    ${TypePrefix}error errorCode;
};

/**
 * Abstract GPU reference smart pointer.
 */
template<typename T>
class ${TypePrefix}ref
{
public:
    ${TypePrefix}ref()
        : pointer(0)
    {
    }

    ${TypePrefix}ref(const ${TypePrefix}ref<T> &other)
    {
        if(other.pointer)
            other.pointer->addReference();
        pointer = other.pointer;
    }

    ${TypePrefix}ref(T* pointer)
        : pointer(0)
    {
		reset(pointer);
    }

    ~${TypePrefix}ref()
    {
        if (pointer)
            pointer->release();
    }

    ${TypePrefix}ref<T> &operator=(T *newPointer)
    {
        if (pointer)
            pointer->release();
        pointer = newPointer;
        return *this;
    }

    ${TypePrefix}ref<T> &operator=(const ${TypePrefix}ref<T> &other)
    {
        if(pointer != other.pointer)
        {
            if(other.pointer)
                other.pointer->addReference();
            if(pointer)
                pointer->release();
            pointer = other.pointer;
        }
        return *this;
    }

	void reset(T *newPointer = nullptr)
	{
		if(pointer)
			pointer->release();
		pointer = newPointer;
	}

    operator bool() const
    {
        return pointer;
    }

    bool operator!() const
    {
        return !pointer;
    }

    T* get() const
    {
        return pointer;
    }

    T *operator->() const
    {
        return pointer;
    }

private:
    T *pointer;
};

/**
 * Helper function to convert an error code into an exception.
 */
inline void $ThrowIfFailed(${TypePrefix}error error)
{
    if(error < 0)
        throw ${TypePrefix}exception(error);
}

"""

HEADER_END = \
"""
#endif /* $HeaderProtectMacro */
"""


# Converts text in 'CamelCase' into 'CAMEL_CASE'
# Snippet taken from: http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
def convertToUnderscore(s):
    return re.sub('(?!^)([0-9A-Z]+)', r'_\1', s).upper().replace('__', '_')

class MakeHeaderVisitor:
    def __init__(self, out):
        self.out = out
        self.variables = {}

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

    def setup(self, api):
        self.api = api
        self.variables = {
            'ApiName': api.name,
            'HeaderProtectMacro': (api.headerFileName + 'pp').upper().replace('.', '_') + '_',
            'CHeader': api.headerFileName,
            'ApiExportMacro': api.constantPrefix + 'EXPORT',
            'ConstantPrefix': api.constantPrefix,
            'FunctionPrefix': api.functionPrefix,
            'TypePrefix': api.typePrefix,
            'ThrowIfFailed': api.functionPrefix + 'ThrowIfFailed'
        }

    def beginHeader(self):
        self.printString(HEADER_START)

    def endHeader(self):
        self.printString(HEADER_END)

    def visitApiDefinition(self, api):
        self.setup(api)
        self.beginHeader();
        self.emitVersions(api.versions)
        self.emitExtensions(api.extensions)
        self.endHeader();

    def convertMethodReturnType(self, typeString):
        if self.api.isInterfaceReference(typeString):
            return self.processText('${TypePrefix}ref<$TypePrefix$Type>', Type=typeString[:-1])
        return self.processText('$TypePrefix$Type', Type=typeString)

    def convertMethodArgumentType(self, typeString):
        if typeString.endswith('**') and self.api.isInterfaceReference(typeString[:-1]):
            return self.processText('${TypePrefix}ref<$TypePrefix$Type>*', Type=typeString[:-2])
        if self.api.isInterfaceReference(typeString):
            return self.processText('const ${TypePrefix}ref<$TypePrefix$Type>&', Type=typeString[:-1])
        return self.processText('$TypePrefix$Type', Type=typeString)

    def emitMethodWrapper(self, function):
        allArguments = function.arguments

        arguments = self.makeArgumentsString(allArguments)
        paramNames = self.makeArgumentNamesString(allArguments)
        if function.returnType == 'error':
            self.printLine('\tinline void $FunctionName($Arguments)',
                ReturnType = function.returnType,
                FunctionName = function.name,
                Arguments = arguments)
            self.printLine('\t{')
            self.printLine('\t\t$ThrowIfFailed($FunctionPrefix$FunctionName($Arguments));', FunctionName = function.cname, Arguments = paramNames)
            self.printLine('\t}')
            self.newline()
        else:
            returnType = self.convertMethodReturnType(function.returnType)
            self.printLine('\tinline $ReturnType $FunctionName($Arguments)',
                ReturnType = returnType,
                FunctionName = function.name,
                Arguments = arguments)
            self.printLine('\t{')
            self.printLine('\t\treturn $FunctionPrefix$FunctionName($Arguments);', FunctionName = function.cname, Arguments = paramNames)
            self.printLine('\t}')
            self.newline()

    def makeArgumentsString(self, arguments):
        # Emit void when no having arguments
        if len(arguments) == 0:
            return ''

        result = ''
        for i in range(len(arguments)):
            arg = arguments[i]
            if i > 0: result += ', '
            result += self.processText('$Type $Name', Type = self.convertMethodArgumentType(arg.type), Name = arg.name)
        return result

    def makeArgumentNamesString(self, arguments):
        result = 'this'
        for i in range(len(arguments)):
            arg = arguments[i]
            typeString = arg.type
            if typeString.endswith('**') and self.api.isInterfaceReference(typeString[:-1]):
                convertedArgument = self.processText('reinterpret_cast<$TypePrefix$Type> ($Arg)', Arg = arg.name, Type=typeString)
            elif self.api.isInterfaceReference(typeString):
                convertedArgument = '%s.get()' % arg.name
            else:
                convertedArgument = arg.name
            result += ', %s' % convertedArgument
        return result

    def emitInterface(self, interface):
        self.printLine('// Interface wrapper for $TypePrefix$Name.', Name = interface.name)
        self.printLine('struct _$TypePrefix$Name', Name = interface.name)
        self.printLine('{')
        self.printLine('private:')
        self.printLine('\t_$TypePrefix$Name() {}', Name = interface.name)
        self.newline()
        self.printLine('public:')
        for method in interface.methods:
            self.emitMethodWrapper(method)
        self.printLine('};')
        self.newline()
        self.printLine('typedef ${TypePrefix}ref<$TypePrefix$Name> $TypePrefix${Name}_ref;', Name = interface.name)
        self.newline()

    def emitFragment(self, fragment):
        # Emit the interface methods
        for interface in fragment.interfaces:
            self.emitInterface(interface)

    def emitVersion(self, version):
        self.emitFragment(version)

    def emitVersions(self, versions):
        for version in versions.values():
            self.emitVersion(version)

    def emitExtension(self, version):
        self.emitFragment(version)

    def emitExtensions(self, extensions):
        for extension in extensions.values():
            self.emitExtension(extension)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "make-headers <definitions> <output dir>"
    else:
        api = ApiDefinition.loadFromFileNamed(sys.argv[1])
        with open(sys.argv[2] + '/' + api.getBindingProperty('C++', 'headerFile'), 'w') as out:
            visitor = MakeHeaderVisitor(out)
            api.accept(visitor)
