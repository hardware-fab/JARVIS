// *************************************************
// Authors              :   Andrea Galimberti (andrea.galimberti@polimi.it),
//                          Davide Galli (davide.galli@polimi.it),
//                          Davide Zoni (davide.zoni@polimi.it)
//
// Other contributor(s) :   Andrea Motta
// *************************************************

#ifndef RND_SCD_H
#define RND_SCD_H

#include <FreeRTOS.h>
#include <task.h>

/* Priorities used by the tasks. */
#define mainQUEUE_RECEIVE_TASK_PRIORITY (tskIDLE_PRIORITY + 2)
#define mainQUEUE_SEND_TASK_PRIORITY (tskIDLE_PRIORITY + 1)

#define mainAES_TASK_PRIOTIY (tskIDLE_PRIORITY + 3)
#define mainPRIO_MANAGER_TASK_PRIOTIY (tskIDLE_PRIORITY)

#define THREAD_COUNT      (4)
#define aesBATCH_SIZE     (1024)

#define INIT_STATE                                                                                     \
    {                                                                                                  \
        0x40, 0x41, 0x40, 0x41, 0x40, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41, 0x41 \
    }
#define TRUE_KEY                                                                                       \
    {                                                                                                  \
        0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6, 0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c \
    }
    
#define PUF_KEY                                                                                        \
    {                                                                                                  \
        /*0xfa, 0x76, 0xc4, 0x08, 0x26, 0xfe, 0x6d, 0x17, 0xab, 0xa7, 0x10, 0x8a, 0x09, 0x2b, 0x87, 0x31*/ \
        0x2a, 0x71, 0x14, 0xb6, 0x3f, 0x1e, 0x02, 0x17, 0xab, 0xf7, 0x10, 0xb8, 0x09, 0xcf, 0x7a, 0x9a \
    }

#endif //RND_SCD_H