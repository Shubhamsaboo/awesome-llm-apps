# 🛡️ Tutorial 6: Guardrails & Validation

Master AI safety and validation with the OpenAI Agents SDK! This tutorial teaches you how to implement input and output guardrails to create safe, reliable AI agents that validate requests and responses before and after agent execution.

## 🎯 What You'll Learn

- **Input Guardrails**: Validate and filter user inputs before processing
- **Output Guardrails**: Check and sanitize agent responses before delivery
- **Guardrail Agents**: Specialized agents for validation and safety checks
- **Tripwire System**: Automatic blocking when validation fails
- **Exception Handling**: Proper error handling for guardrail violations
- **Production Safety**: Real-world patterns for AI safety in production

## 🧠 Core Concept: What are Guardrails?

Guardrails are **automated safety mechanisms** that validate inputs and outputs to ensure AI agents operate within acceptable boundaries. Think of guardrails as **safety checkpoints** that:

- Prevent processing of inappropriate or harmful content
- Block responses that violate safety policies
- Validate inputs against business rules and constraints
- Ensure compliance with content policies
- Provide automatic error handling and user feedback

## 🚀 Key Guardrails Concepts

### **Input Guardrails**
Validate user inputs before agent processing:

```python
@input_guardrail
async def content_filter(ctx, agent, input) -> GuardrailFunctionOutput:
    # Check if input violates policies
    if is_inappropriate(input):
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info="Content blocked for safety"
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)
```

### **Output Guardrails**
Validate agent responses before delivery:

```python
@output_guardrail
async def response_filter(ctx, agent, output) -> GuardrailFunctionOutput:
    # Check if response contains sensitive data
    if contains_sensitive_info(output):
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info="Response blocked for safety"
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)
```

### **Guardrail Agents**
Specialized agents for validation logic:

```python
validation_agent = Agent(
    name="Content Validator",
    instructions="Check content for safety violations",
    output_type=SafetyCheck
)
```

## 🧪 What This Demonstrates

### **1. Math Homework Detection**
- Input guardrail that detects academic homework requests
- Confidence-based blocking with threshold validation
- Structured output validation with Pydantic models

### **2. Content Safety Validation**
- Output guardrail for inappropriate content detection
- Severity-based filtering (low, medium, high)
- Automated response blocking for policy violations

### **3. Exception Handling**
- `InputGuardrailTripwireTriggered` exception handling
- `OutputGuardrailTripwireTriggered` exception handling
- Graceful error recovery and user feedback

### **4. Guardrail Integration**
- Seamless integration with existing agent workflows
- Multiple guardrails on single agent
- Custom validation logic with business rules

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to implement input validation to filter requests
- ✅ Creating output guardrails for response safety
- ✅ Building specialized guardrail agents for validation
- ✅ Handling guardrail exceptions gracefully
- ✅ Production-ready safety patterns for AI applications

## 🚀 Getting Started

1. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

2. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the guardrails example**:
   ```python
   import asyncio
   from agent import guardrails_example, test_input_guardrail
   
   # Test guardrails system
   asyncio.run(guardrails_example())
   asyncio.run(test_input_guardrail())
   ```

## 🧪 Sample Use Cases

### Input Guardrail Testing
- "How do I reset my password?" ✅ (Should pass)
- "Can you solve this equation: 2x + 5 = 15?" 🚫 (Should trigger homework detection)
- "What are your product features?" ✅ (Should pass)

### Output Guardrail Testing
- Normal customer support responses ✅
- Responses containing sensitive information 🚫
- Policy-violating content 🚫

### Exception Scenarios
- Graceful handling of blocked requests
- User-friendly error messages
- Logging and monitoring of guardrail violations

## 🔧 Key Guardrail Patterns

### 1. **Input Validation Pattern**
```python
@input_guardrail
async def validate_input(ctx, agent, input) -> GuardrailFunctionOutput:
    validation_result = await validate_with_ai(input)
    return GuardrailFunctionOutput(
        tripwire_triggered=validation_result.is_violation,
        output_info=validation_result.details
    )
```

### 2. **Output Safety Pattern**
```python
@output_guardrail
async def safety_check(ctx, agent, output) -> GuardrailFunctionOutput:
    safety_result = await check_safety(output.response)
    return GuardrailFunctionOutput(
        tripwire_triggered=safety_result.is_unsafe,
        output_info=safety_result.reason
    )
```

### 3. **Exception Handling Pattern**
```python
try:
    result = await Runner.run(protected_agent, user_input)
    return result.final_output
except InputGuardrailTripwireTriggered as e:
    return "Request blocked by safety filters"
except OutputGuardrailTripwireTriggered as e:
    return "Response blocked for safety reasons"
```

### 4. **Confidence-Based Blocking**
```python
return GuardrailFunctionOutput(
    tripwire_triggered=violation_detected and confidence > 0.7,
    output_info={"confidence": confidence, "reason": reason}
)
```

## 💡 Guardrails Best Practices

1. **Layered Defense**: Use both input and output guardrails for comprehensive protection
2. **Confidence Thresholds**: Implement confidence-based blocking to reduce false positives
3. **Clear Messaging**: Provide helpful error messages that guide users to appropriate requests
4. **Performance Optimization**: Cache validation results and use efficient validation models
5. **Monitoring & Logging**: Track guardrail violations for system improvement

## 🔧 Advanced Patterns

### **Multi-Level Validation**
```python
agent = Agent(
    name="Protected Agent",
    input_guardrails=[content_filter, spam_detector, policy_checker],
    output_guardrails=[safety_validator, privacy_filter]
)
```

### **Context-Aware Guardrails**
```python
@input_guardrail
async def user_context_validator(ctx: RunContextWrapper[UserInfo], agent, input):
    user = ctx.context
    # Validate based on user permissions or context
    if user.permission_level < required_level:
        return GuardrailFunctionOutput(tripwire_triggered=True)
```

### **Business Rule Validation**
```python
@input_guardrail
async def business_rules(ctx, agent, input) -> GuardrailFunctionOutput:
    # Validate against business constraints
    if violates_business_rules(input):
        return GuardrailFunctionOutput(
            tripwire_triggered=True,
            output_info="Request violates business policies"
        )
```

## 🚨 Common Pitfalls

- **Over-Blocking**: Setting thresholds too low can block legitimate requests
- **Under-Blocking**: Setting thresholds too high may allow harmful content
- **Performance Impact**: Heavy validation can slow response times
- **False Positives**: Poorly trained validation models may block valid requests

## 💡 Pro Tips

- **Test Thoroughly**: Create comprehensive test suites for guardrail validation
- **Monitor Metrics**: Track false positive and false negative rates
- **Iterative Improvement**: Continuously refine validation logic based on real usage
- **User Feedback**: Implement appeals process for blocked requests
- **Gradual Rollout**: Deploy new guardrails gradually with monitoring

## 🔗 Production Considerations

### **Scalability**
- Use efficient validation models
- Implement caching for repeated validations
- Consider async validation for better performance

### **Monitoring**
- Log all guardrail decisions for analysis
- Track violation patterns and trends
- Monitor system performance impact

### **Compliance**
- Align guardrails with regulatory requirements
- Implement audit trails for compliance reporting
- Regular review and updates of validation rules

## 🔗 Next Steps

After mastering guardrails, you'll be ready for:
- **[Tutorial 7: Sessions](../7_sessions/README.md)** - Combining safety with conversation memory
- **[Tutorial 8: Production Patterns](../8_production_patterns/README.md)** - Scaling guardrails in production
- **[Tutorial 9: Advanced Security](../9_advanced_security/README.md)** - Enterprise-grade AI safety patterns
