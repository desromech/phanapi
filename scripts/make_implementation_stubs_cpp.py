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

namespace $Namespace
{

extern $IcdDispatchTableType cppRefcountedDispatchTable;

/**
 * Phanapi reference counter
 */
template <typename T>
class ref_counter
{
public:
    ref_counter(T *cobject)
        : dispatchTable(&cppRefcountedDispatchTable), object(cobject), strongCount(1), weakCount(0)
    {
    }

    $ErrorType retain()
    {
        // Check once before doing the increase.
        if(strongCount == 0)
            return $ErrorInvalidOperation;

        // Increase the referenece count.
        auto old = strongCount.fetch_add(1, std::memory_order_relaxed);

        // Check again, for concurrency reasons.
        if(strongCount == 0)
            return $ErrorInvalidOperation;

        return $ErrorOk;
    }

    $ErrorType release()
    {
        // First sanity check.
        if(strongCount == 0)
            return $ErrorInvalidOperation;

        // Decrease the strong count.
        auto old = strongCount.fetch_sub(1, std::memory_order_relaxed);

        // Check again, for concurrency reasons.
        if(old == 0)
            return $ErrorInvalidOperation;

        // Should I delete the object?
        if(old == 1)
            delete object;

        // Should I delete myself?
        if(weakCount == 0)
            delete this;

        return $ErrorOk;
    }

    bool weakLock()
    {
        while((auto oldCount = strongCount.load()) != 0)
        {
            if(strongCount.compare_exchange_weak(oldCount, oldCount + 1))
                return true;
        }

        return false;
    }

    void weakRetain()
    {
    }

    void weakRelease()
    {
    }

    $IcdDispatchTableType dispatchTable;
    T * object;
    std::atomic_uint strongCount;
    std::atomic_uint weakCount;
};

class base_interface
{
public
    virtual ~base_interface() {}
};

} // End of namespace $Namespace

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
        self.namespace = api.getBindingProperty('C++/Impl', 'namespace')
        self.variables = {
            'ApiName': api.name,
            'HeaderProtectMacro': (api.headerFileName + 'pp').upper().replace('.', '_') + '_',
            'CHeader': api.headerFileName,
            'ApiExportMacro': api.constantPrefix + 'EXPORT',
            'ConstantPrefix': api.constantPrefix,
            'FunctionPrefix': api.functionPrefix,
            'Namespace': self.namespace,
            'TypePrefix': api.typePrefix,
            'ThrowIfFailed': api.functionPrefix + 'ThrowIfFailed',

            'ErrorType': api.typePrefix + 'error',
            'IcdDispatchTableType': api.typePrefix + 'icd_dispatch',
            'ErrorOk': api.constantPrefix + 'INVALID_OK',
            'ErrorInvalidOperation': api.constantPrefix + 'INVALID_OPERATION',
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

    def emitVirtualMethod(self, function):
        if function.name in ['addReference', 'release']:
            return

        allArguments = function.arguments

        arguments = self.makeArgumentsString(allArguments)
        paramNames = self.makeArgumentNamesString(allArguments)
        self.printLine('\tvirtual $ReturnType $FunctionName ( $Arguments ) = 0;',
                ReturnType = self.convertMethodReturnType(function.returnType),
                FunctionName = function.name,
                Arguments = arguments)

    def convertMethodReturnType(self, typeString):
        if self.api.isInterfaceReference(typeString):
            return typeString[:-1] + '_ref'
        return self.processText('$TypePrefix$Type', Type=typeString)

    def convertMethodArgumentType(self, typeString):
        if typeString.endswith('**') and self.api.isInterfaceReference(typeString[:-1]):
            return typeString[:-2] + '_ref*'
        if self.api.isInterfaceReference(typeString):
            return typeString[:-1] + '_ref'
        return self.processText('$TypePrefix$Type', Type=typeString)

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
            result += ', %s' % arg.name
        return result

    def beginNamespace(self):
        self.printLine('namespace $Namespace')
        self.printLine('{')

    def endNamespace(self):
        self.printLine('} // End of $Namespace')

    def declareInterface(self, interface):
        self.printLine('struct $Name;', Name = interface.name)
        self.printLine('typedef ref<$Name> ${Name}_ref;', Name = interface.name)
        self.printLine('typedef weakref<$Name> ${Name}_weakref;', Name = interface.name)
        self.newline()

    def emitInterface(self, interface):
        self.printLine('// Interface wrapper for $TypePrefix$Name.', Name = interface.name)
        self.printLine('struct $Name : base_interface', Name = interface.name)
        self.printLine('{')
        self.printLine('public:')
        for method in interface.methods:
            self.emitVirtualMethod(method)
        self.printLine('};')
        self.newline()
        self.newline()

    def emitFragment(self, fragment):
        self.beginNamespace();

        # Declare the interfaces
        for interface in fragment.interfaces:
            self.declareInterface(interface)

        # Emit the interface bodies
        for interface in fragment.interfaces:
            self.emitInterface(interface)
        self.endNamespace();

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
        with open(sys.argv[2] + '/' + api.getBindingProperty('C++/Impl', 'headerFile'), 'w') as out:
            visitor = MakeHeaderVisitor(out)
            api.accept(visitor)
