// *************************************************
// Authors              :   Andrea Galimberti (andrea.galimberti@polimi.it),
//                          Davide Galli (davide.galli@polimi.it),
//                          Davide Zoni (davide.zoni@polimi.it)
//
// Other contributor(s) :   Andrea Motta
// *************************************************

/* FreeRTOS kernel includes. */
#include <FreeRTOS.h>
#include <task.h>
#include <queue.h>

#include <stdio.h>
#include <stdint.h>

#include "random_scheduler.h"
#include "trng.h"

#define AES_keyExpSize 176

uint8_t init_state[16] = INIT_STATE;
uint8_t true_key[16] = TRUE_KEY;

typedef uint8_t state_t[4][4];
struct AES_ctx
{
    uint8_t RoundKey[AES_keyExpSize];
};

typedef struct aes_cb
{
    uint8_t tag;
    struct AES_ctx *key;
    state_t *state;
    uint8_t finished;
    TaskHandle_t task;
} aes_cb_t;

state_t states[THREAD_COUNT];
struct AES_ctx full_keys[THREAD_COUNT];
aes_cb_t aes_CB[THREAD_COUNT];
uint32_t aes_finished_count = THREAD_COUNT;

extern void aes_run(uint8_t *state, uint8_t *key);
extern void AES_init_ctx(struct AES_ctx *ctx, const uint8_t *key);
extern void CipherMasked(state_t *state, const uint8_t *RoundKey);
extern void CipherMasked_round(state_t *state, const uint8_t *RoundKey, uint8_t round);

/*
 * AES environment setup, generates necessary aes states and keys:
 *	a state and key pair for the real aes
 *	THREAD_COUNT-1 state and key pairs for the chaff ones, each key is generated running a puf N times,
 *	with N being different for each key
 */
static void aesSetup()
{
    uint8_t puf[16] = PUF_KEY;
    uint8_t temp_key[16];

    AES_init_ctx(&full_keys[0], true_key);

    for (uint8_t i = 0; i < THREAD_COUNT; i++)
    {
        for (uint8_t j = 0; j < 16; j++)
        {
            states[i][j % 4][j / 4] = init_state[j];
        }
    }

    for (uint8_t i = 1; i < THREAD_COUNT; i++)
    {
        for (uint8_t j = 0; j < 16; j++)
        {
            temp_key[j] = full_keys[i - 1].RoundKey[j];
        }
        aes_run(temp_key, puf);
        AES_init_ctx(&full_keys[i], true_key);
    }
}

static void prvEncoderTask_delay(void *pvParameters)
{
    aes_cb_t *aes_current_cb = (aes_cb_t *)pvParameters;

    while (1)
    {
        CipherMasked_round((state_t *)aes_current_cb->state, aes_current_cb->key->RoundKey, (trng() % 4) + 1);

        portENTER_CRITICAL();
        aes_current_cb->finished = 1;
        portEXIT_CRITICAL();
        while (aes_current_cb->finished)
        {
            vTaskSuspend(aes_current_cb->task);
            taskYIELD()
        }
    }
}

static void prvEncoderTask(void *pvParameters)
{
    aes_cb_t *aes_current_cb = (aes_cb_t *)pvParameters;

    while (1)
    {
        CipherMasked((state_t *)aes_current_cb->state, aes_current_cb->key->RoundKey);

        portENTER_CRITICAL();

        aes_current_cb->finished = 1;

        if (aes_current_cb->tag == 0)
        {
            aes_finished_count = 1;
            for (int i = 1; i < THREAD_COUNT; i++)
                vTaskSuspend(aes_CB[i].task);
        }

        portEXIT_CRITICAL();
        while (aes_current_cb->finished)
        {
            vTaskSuspend(aes_current_cb->task);
        }
    }
}

uint32_t delay;
static void prvPriorityManagerTask(void *pvParameters)
{
    aes_cb_t *aes_current_cb = (aes_cb_t *)pvParameters;

    for (uint16_t run_number = 0; run_number < aesBATCH_SIZE; run_number++)
    {
        vTaskSuspendAll();

        for (uint8_t i = 0; i < THREAD_COUNT; i++)
        {
            aes_current_cb[i].finished = 0;
            // merge all chaff AES states with true-key one
            for (uint8_t j = 0; j < 4; j++) {
                for (uint8_t k = 0; k < 4; k++)
                {
                    (*aes_current_cb[i].state)[j][k] = (*aes_current_cb[0].state)[j][k];
                }
            }
            if (i == THREAD_COUNT - 1)
            {
                xTaskCreate(
                    prvEncoderTask_delay,
                    "DELAY",
                    configMINIMAL_STACK_SIZE * 2U,
                    (void *)&(aes_current_cb[i]),
                    mainAES_TASK_PRIOTIY + 1,
                    &(aes_current_cb[i].task));
            }
            else
            {
                xTaskCreate(
                    prvEncoderTask,
                    "AES",
                    configMINIMAL_STACK_SIZE * 2U,
                    (void *)&(aes_current_cb[i]),
                    mainAES_TASK_PRIOTIY,
                    &(aes_current_cb[i].task));
            }
        }
        aes_finished_count = 0;

        //+++++++++++ Rise trigger ++++++++++++
        asm(".RISE_TRG:");
        xTaskResumeAll();

        while (aes_current_cb[0].finished == 0)
        {
            taskYIELD()
        };
        //+++++++++++ Fall trigger ++++++++++++
        asm(".FALL_TRG:");
        for (uint8_t i = 0; i < THREAD_COUNT; i++)
        {
            vTaskDelete(aes_CB[i].task);
            aes_CB[i].finished = 0;
        }
        for (delay = 0; delay < 50000; delay++)
            ;
    }

    portDISABLE_INTERRUPTS();
    asm(".END_BATCH:");
    while (1)
        ;
}

int chaff_masked(void)
{
    aesSetup();
    xTaskCreate(
        prvPriorityManagerTask,
        "PRIORITY MANAGER",
        configMINIMAL_STACK_SIZE * 2U,
        (void *)aes_CB,
        mainPRIO_MANAGER_TASK_PRIOTIY,
        NULL);
    for (uint8_t i = 0; i < THREAD_COUNT; i++)
    {
        aes_CB[i].tag = i;
        aes_CB[i].key = &full_keys[i];
        aes_CB[i].state = &states[i];
        aes_CB[i].finished = 0;
    }

    aes_CB[0].state = (state_t *) init_state;

    vTaskStartScheduler();

    return 0;
}

