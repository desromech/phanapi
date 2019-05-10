#!/usr/bin/python
import re
import sys

from definition import *
from string import Template


HEADER_START = \
"""
#ifndef $HeaderProtectMacro
#define $HeaderProtectMacro

#include "$CHeader"
#include <stdexcept>
#include <memory>
#include <atomic>

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
        object->setRefCounterPointer(this);
    }

    $ErrorType retain()
    {
        // Check once before doing the increase.
        if(strongCount == 0)
            return $ErrorInvalidOperation;

        // Increase the referenece count.
        auto old = strongCount.fetch_add(1, std::memory_order_relaxed);

        // Check again, for concurrency reasons.
        if(old == 0)
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
        {
            delete object;

            // Should I delete myself?
            if(weakCount == 0)
                delete this;
        }

        return $ErrorOk;
    }

    bool weakLock()
    {
        unsigned int oldCount;
        while((oldCount = strongCount.load()) != 0)
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

    $IcdDispatchTableType *dispatchTable;
    T * object;
    std::atomic_uint strongCount;
    std::atomic_uint weakCount;
};

template<typename T>
class weak_ref;

/**
 * Phanapi strong reference
 */
template<typename T>
class ref
{
public:
    typedef ref_counter<T> Counter;
    typedef ref<T> StrongRef;
    typedef weak_ref<T> WeakRef;

private:
    Counter *counter;
    friend WeakRef;

public:
    ref() : counter(nullptr) {}

    ref(const StrongRef &other)
        : counter(nullptr)
    {
        *this = other;
    }

    explicit ref(Counter *theCounter)
        : counter(theCounter)
    {
    }

    ~ref()
    {
        if(counter)
            counter->release();
    }

    static StrongRef import(void *rawCounter)
    {
        auto castedCounter = reinterpret_cast<Counter*> (rawCounter);
        if(castedCounter)
            castedCounter->retain();
        return StrongRef(castedCounter);
    }

    StrongRef &operator=(const StrongRef &other)
    {
        auto newCounter = other.counter;
        if(newCounter)
            newCounter->retain();
        if(counter)
            counter->release();
        counter = newCounter;
        return *this;
    }

    void reset(Counter *newCounter = nullptr)
    {
        if(counter)
            counter->release();
        counter = newCounter;
    }

    Counter *disown()
    {
        Counter *result = counter;
        counter = nullptr;
        return result;
    }

    Counter *disownedNewRef() const
    {
        if(counter)
            counter->retain();
        return counter;
    }

    Counter *asPtrWithoutNewRef() const
    {
        return counter;
    }

    template<typename U>
    U *as() const
    {
        return static_cast<U*> (counter->object);
    }

    T *get() const
    {
        return counter ? counter->object : nullptr;
    }

    T *operator->() const
    {
        return counter->object;
    }

    operator bool() const
    {
        return counter != nullptr;
    }

    bool operator==(const StrongRef &other) const
    {
        return counter == other.counter;
    }

    bool operator<(const StrongRef &other) const
    {
        return counter < other.counter;
    }

    size_t hash() const
    {
        return std::hash<Counter*> () (counter);
    }
};

/**
 * Phanapi weak reference
 */
template<typename T>
class weak_ref
{
public:
    typedef ref_counter<T> Counter;
    typedef ref<T> StrongRef;
    typedef weak_ref<T> WeakRef;

private:
    Counter *counter;

public:
    weak_ref()
        : counter(nullptr) {}

    explicit weak_ref(const StrongRef &ref)
    {
        counter = ref.counter;
        if(counter)
            counter->weakRetain();
    }

    weak_ref(const WeakRef &ref)
    {
        counter = ref.counter;
        if(counter)
            counter->weakRetain();
    }

    ~weak_ref()
    {
        if(counter)
            counter->weakRelease();
    }

    WeakRef &operator=(const StrongRef &other)
    {
        auto newCounter = other.counter;
        if(newCounter)
            newCounter->weakRetain();
        if(counter)
            counter->weakRelease();
        counter = newCounter;
        return *this;
    }

    WeakRef &operator=(const WeakRef &other)
    {
        auto newCounter = other.counter;
        if(newCounter)
            newCounter->weakRetain();
        if(counter)
            counter->weakRelease();
        counter = newCounter;
        return *this;
    }

    StrongRef lock()
    {
        if(!counter)
            return StrongRef();

        return counter->weakLock() ? StrongRef(counter) : StrongRef();
    }

    bool operator==(const WeakRef &other) const
    {
        return counter == other.counter;
    }

    bool operator<(const WeakRef &other) const
    {
        return counter < other.counter;
    }

    size_t hash() const
    {
        return std::hash<Counter*> () (counter);
    }
};

template<typename I, typename T, typename...Args>
inline ref<I> makeObjectWithInterface(Args... args)
{
    std::unique_ptr<T> object(new T(args...));
    std::unique_ptr<ref_counter<I>> counter(new ref_counter<I> (object.release()));
    return ref<I> (counter.release());
}

template<typename T, typename...Args>
inline ref<typename T::main_interface> makeObject(Args... args)
{
   return makeObjectWithInterface<typename T::main_interface, T> (args...);
}

/**
 * Phanapi base interface
 */
class base_interface
{
public:
    virtual ~base_interface() {}

    void setRefCounterPointer(void *newPointer)
    {
        myRefCounter = newPointer;
    }

    template<typename T=base_interface>
    const ref<T> &refFromThis()
    {
        return reinterpret_cast<const ref<T> &> (myRefCounter);
    }

private:
    void *myRefCounter;
};

} // End of namespace $Namespace

namespace std
{
template<typename T>
struct hash<$Namespace::ref<T>>
{
    size_t operator()(const $Namespace::ref<T> &ref) const
    {
        return ref.hash();
    }
};

template<typename T>
struct hash<$Namespace::weak_ref<T>>
{
    size_t operator()(const $Namespace::ref<T> &ref) const
    {
        return ref.hash();
    }
};

}

"""

HEADER_END = \
"""
#endif /* $HeaderProtectMacro */
"""

DISPATCH_FILE_START = \
"""
#include "$CPPHeader"

inline void* hideType(void *t)
{
	return t;
}

#define asRef(O, I) (*reinterpret_cast<$Namespace::ref<O> *> (hideType(&I)) )
#define asRefCounter(O, I) (reinterpret_cast<$Namespace::ref_counter<O> *> (I))

"""

DISPATCH_FILE_END = \
"""

#undef asRef
#undef asRefCounter

namespace $Namespace
{
$IcdDispatchTableType cppRefcountedDispatchTable = {
#include "$ICDHeader"
};
} // End of $Namespace
"""

# Converts text in 'CamelCase' into 'CAMEL_CASE'
# Snippet taken from: http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
def convertToUnderscore(s):
    return re.sub('(?!^)([0-9A-Z]+)', r'_\1', s).upper().replace('__', '_')

class MakeImplVisitor:
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
            'CPPHeader': api.getBindingProperty('C++/Impl', 'headerFile'),
            'ICDHeader': api.getBindingProperty('C', 'icdIncludeFile'),
            'ApiExportMacro': api.constantPrefix + 'EXPORT',
            'ConstantPrefix': api.constantPrefix,
            'FunctionPrefix': api.functionPrefix,
            'Namespace': self.namespace,
            'TypePrefix': api.typePrefix,
            'ThrowIfFailed': api.functionPrefix + 'ThrowIfFailed',

            'ErrorType': api.typePrefix + 'error',
            'IcdDispatchTableType': api.typePrefix + 'icd_dispatch',
            'ErrorOk': api.constantPrefix + 'OK',
            'ErrorInvalidOperation': api.constantPrefix + 'INVALID_OPERATION',
            'ErrorNullPointer': api.constantPrefix + 'NULL_POINTER',
        }


class MakeHeaderVisitor(MakeImplVisitor):
    def __init__(self, out):
        MakeImplVisitor.__init__(self, out)

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
        self.printLine('\tvirtual $ReturnType $FunctionName($Arguments) = 0;',
                ReturnType = self.convertMethodReturnType(function.returnType),
                FunctionName = function.name,
                Arguments = arguments)

    def convertMethodReturnType(self, typeString):
        if self.api.isInterfaceReference(typeString):
            return typeString[:-1] + '_ptr'
        return self.processText('$TypePrefix$Type', Type=typeString)

    def convertMethodArgumentType(self, typeString):
        if typeString.endswith('**') and self.api.isInterfaceReference(typeString[:-1]):
            return typeString[:-2] + '_ref*'
        if self.api.isInterfaceReference(typeString):
            return 'const ' + typeString[:-1] + '_ref &'
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
        self.printLine('typedef ref_counter<$Name> *${Name}_ptr;', Name = interface.name)
        self.printLine('typedef ref<$Name> ${Name}_ref;', Name = interface.name)
        self.printLine('typedef weak_ref<$Name> ${Name}_weakref;', Name = interface.name)
        self.newline()

    def emitInterface(self, interface):
        self.printLine('// Interface wrapper for $TypePrefix$Name.', Name = interface.name)
        self.printLine('struct $Name : base_interface', Name = interface.name)
        self.printLine('{')
        self.printLine('public:')
        self.printLine('\ttypedef $Name main_interface;', Name = interface.name)
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

class MakeDispatchVisitor(MakeImplVisitor):
    def __init__(self, out):
        MakeImplVisitor.__init__(self, out)

    def beginDispatchFile(self):
        self.printString(DISPATCH_FILE_START)

    def endDispatchFile(self):
        self.printString(DISPATCH_FILE_END)

    def visitApiDefinition(self, api):
        self.setup(api)
        self.beginDispatchFile();
        self.emitVersions(api.versions)
        self.emitExtensions(api.extensions)
        self.endDispatchFile();

    def emitCheckSelfInFunction(self, function):
        if function.returnType == "error":
            self.printLine("\tif(!self) return $ErrorNullPointer;")
    
    def emitDispatchFunction(self, function):
        assert function.clazz is not None

        allArguments = [SelfArgument(function.clazz)] + function.arguments
        allArguments[0].name = "self"

        arguments = self.makePrototypeArgumentsString(allArguments)
        self.printLine('${ApiExportMacro} $TypePrefix$ReturnType $FunctionPrefix$FunctionName($Arguments)',
            ReturnType = function.returnType,
            FunctionName = function.cname,
            Arguments = arguments)
        self.printLine('{')
        if function.name == "addReference":
            self.emitCheckSelfInFunction(function)
            self.printLine('\treturn asRefCounter($Namespace::$Class, self)->retain();', Class = function.clazz.name);
        elif function.name == "release":
            self.emitCheckSelfInFunction(function)
            self.printLine('\treturn asRefCounter($Namespace::$Class, self)->release();', Class = function.clazz.name);
        else:
            self.emitCheckSelfInFunction(function)
            callExpression = self.processText('asRef($Namespace::$Class, self)->$MethodName($Arguments)',
                Class = function.clazz.name,
                MethodName = function.name,
                Arguments = self.makeDispatchCallArgumentsString(function.arguments)
            )

            if self.api.isInterfaceReference(function.returnType):
                self.printLine("\treturn reinterpret_cast<$TypePrefix$ReturnType> ($CallExpression);",
                    ReturnType = function.returnType,
                    CallExpression = callExpression
                )
            else:
                self.printLine("\treturn $CallExpression;", CallExpression = callExpression)
        self.printLine('}')
        self.newline()

    def makePrototypeArgumentsString(self, arguments):
        # Emit void when no having arguments
        if len(arguments) == 0:
            return 'void'

        result = ''
        for i in range(len(arguments)):
            arg = arguments[i]
            if i > 0: result += ', '
            result += self.processText('$TypePrefix$Type $Name', Type = arg.type, Name = arg.name)
        return result

    def makeDispatchCallArgumentsString(self, arguments):
        result = ''
        for i in range(len(arguments)):
            arg = arguments[i]
            if i > 0: result += ', '

            typeString = arg.type
            if typeString.endswith('**') and self.api.isInterfaceReference(typeString[:-1]):
                result += self.processText('reinterpret_cast<$Namespace::$TargetType> ($Arg)',
                    TargetType = typeString[:-2] + '_ref*',
                    Arg = arg.name
                )
            elif self.api.isInterfaceReference(typeString):
                result += self.processText('asRef($Namespace::$Type, $Arg)', Type = arg.type[:-1], Arg = arg.name)
            else:
                result += arg.name

        return result

    def emitInterface(self, interface):
        self.printLine("//==============================================================================")
        self.printLine("// $iface C dispatching functions.", iface = interface.name)
        self.printLine("//==============================================================================")
        self.newline()

        for method in interface.methods:
            self.emitDispatchFunction(method)


    def emitFragment(self, fragment):
        # Emit the interface bodies
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

        with open(sys.argv[2] + '/' + api.getBindingProperty('C++/Impl', 'headerFile'), 'w') as out:
            visitor = MakeHeaderVisitor(out)
            api.accept(visitor)

        with open(sys.argv[2] + '/' + api.getBindingProperty('C++/Impl', 'dispatchIncludeFile'), 'w') as out:
            visitor = MakeDispatchVisitor(out)
            api.accept(visitor)
